# experiments/tasks.py
import subprocess
import os
from celery import shared_task
from .models import SparkExperiment

# As defined in the docker-compose.yml
SHARED_DIR = os.environ.get('SPARK_SHARED_DIR', '/opt/spark/apps')


@shared_task
def run_db_script(experiment_id):
    experiment = SparkExperiment.objects.select_related('script', 'dataset').get(id=experiment_id)
    experiment.status = 'Running'
    experiment.output = ""
    experiment.save()

    # Define the shared directory path for the script.
    filename = f"experiment_{experiment.id}.{experiment.script.file_type}"
    tmp_path = os.path.join(SHARED_DIR, filename)

    try:
        # Write the script content directly to the shared volume
        with open(tmp_path, 'w' if experiment.script.file_type != 'jar' else 'wb') as f:
            f.write(experiment.script.content)

        cmd = ['spark-submit', '--master', 'spark://spark-master:7077', tmp_path]

        if experiment.script.file_type == 'jar' and experiment.script.main_class:
            cmd.extend(['--class', experiment.script.main_class])

        #TODO update scripts so they observe this standard.
        # FIXED: Pass the dataset path as the first argument to the script
        if experiment.dataset and experiment.dataset.file:
            cmd.append(experiment.dataset.get_file_path())

        # Start process with piped output
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        log_buffer = []
        for line in iter(process.stdout.readline, ''):
            log_buffer.append(line)
            if len(log_buffer) >= 20:
                experiment.output += "".join(log_buffer)
                experiment.save(update_fields=['output'])
                log_buffer = []

        experiment.output += "".join(log_buffer)
        experiment.save(update_fields=['output'])

        process.wait()
        experiment.status = 'Success' if process.returncode == 0 else 'Failed'

    except Exception as e:
        experiment.output += f"\nInternal Error: {str(e)}"
        experiment.status = 'Failed'
    finally:
        # 1. Clean up the script file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

        # 2. Check for results.txt in the shared directory and rename/move it
        # Note: Your spark script must be coded to save output to this SHARED_DIR!
        spark_result_file = os.path.join(SHARED_DIR, "results.txt")
        final_result_name = f"{experiment_id}_results.txt"

        if os.path.exists(spark_result_file):
            # Rename it so it doesn't get overwritten by the next experiment
            os.rename(spark_result_file, os.path.join(SHARED_DIR, final_result_name))
            experiment.output += f"\n[System: Successfully saved {final_result_name}]"
        else:
            experiment.output += "\n[System: No results.txt found in shared directory.]"

        experiment.save()