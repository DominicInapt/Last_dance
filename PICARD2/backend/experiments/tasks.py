# backend/experiments/tasks.py
import os
import requests
from celery import shared_task
from .models import SparkExperiment

SHARED_DIR = os.environ.get('SPARK_SHARED_DIR', '/opt/spark/apps')


@shared_task
def run_db_script(experiment_id):
    experiment = SparkExperiment.objects.select_related('script', 'dataset').get(id=experiment_id)
    experiment.status = 'Running'

    # 1. Get the exact, deterministic paths from your model
    script_path = experiment.script.get_absolute_file_path()
    output_path = experiment.get_absolute_output_path()
    result_path = experiment.get_absolute_result_path()

    # 2. Ensure directories exist before trying to write
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    os.makedirs(os.path.dirname(result_path), exist_ok=True)

    # 3. Manually set the relative path string on the model if it's empty
    if not experiment.output:
        experiment.output.name = f'files/output/{experiment.id}.txt'

    experiment.save()

    # Use standard Python open() in append mode - Django's storage is bypassed entirely
    with open(output_path, 'a') as f:
        f.write("\n\n" + "=" * 40 + "\n")
        f.write("        STARTING NEW RUN\n")
        f.write("=" * 40 + "\n\n")

    unique_result_filename = f"results_{experiment.id}.txt"
    spark_result_file = os.path.join(SHARED_DIR, unique_result_filename)

    try:
        args = []
        if experiment.dataset and experiment.dataset.file:
            args.append(experiment.dataset.get_absolute_file_path())
        args.append(spark_result_file)

        response = requests.post(
            'http://spark-master:8080/execute',
            json={'script_path': script_path, 'args': args},
            stream=True
        )

        return_code = -1
        with open(output_path, 'a') as f:
            for line in response.iter_lines(decode_unicode=True):
                if line.startswith("__EXIT_CODE__:"):
                    return_code = int(line.split(":")[1])
                elif line:
                    f.write(line + '\n')
                    f.flush()

        experiment.status = 'Success' if return_code == 0 else 'Failed'

    except Exception as e:
        with open(output_path, 'a') as f:
            f.write(f"\nInternal Error: {str(e)}")
        experiment.status = 'Failed'
    finally:
        # 4. Handle Result File Manually
        if os.path.exists(spark_result_file):
            # Open the exact path in append-binary mode
            with open(result_path, 'ab') as existing_file:
                with open(spark_result_file, 'rb') as new_file:
                    if experiment.result:
                        # Add a visual separator if a result already existed
                        existing_file.write(b"\n\n========================================\n")
                        existing_file.write(b"        RERUN RESULTS\n")
                        existing_file.write(b"========================================\n\n")
                    existing_file.write(new_file.read())

            # Set the relative path string on the model if it's empty
            if not experiment.result:
                experiment.result.name = f'files/results/{experiment.id}.txt'

            os.remove(spark_result_file)

            with open(output_path, 'a') as f:
                f.write(f"\n[System: Successfully appended results to backend storage.]")
        else:
            with open(output_path, 'a') as f:
                f.write(f"\n[System: No {unique_result_filename} found in shared directory.]")

        # Finally, save the model state (this saves the strings to the DB, not the files)
        experiment.save()