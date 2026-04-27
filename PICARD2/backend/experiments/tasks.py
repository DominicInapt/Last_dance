# experiments/tasks.py
import subprocess
import tempfile
import os, sys
from celery import shared_task
from .models import SparkExperiment, Script

#As defined in the docker-compose.yml
SHARED_DIR = os.environ.get('SPARK_SHARED_DIR', '/opt/spark/apps')
SPARK_CONTAINER = os.environ.get('SPARK_CONTAINER', 'PICARD2-spark-master-1')
def copy_from_docker(container_name, container_path, local_path):
    # Step 1: Check if the file exists inside the container
    # 'test -f' quietly returns an exit code of 0 if the file exists, 1 if it doesn't.
    print(f"Checking for '{container_path}' in container '{container_name}'...")
    check_cmd = ['docker', 'exec', container_name, 'test', '-f', container_path]

    try:
        result = subprocess.run(check_cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"⚠️  Warning: File '{container_path}' does not exist in container '{container_name}'.")
            print("Skipping copy operation.")
            return

        print("✅ File found. Initiating copy...")

        # Step 2: Copy the file using docker cp
        copy_cmd = ['docker', 'cp', f"{container_name}:{container_path}", local_path]
        copy_result = subprocess.run(copy_cmd, capture_output=True, text=True)

        if copy_result.returncode == 0:
            print(f"🎉 Successfully copied to '{local_path}'!")
        else:
            print(f"Failed to copy file. Docker error:\n{copy_result.stderr}", file=sys.stderr)

    except FileNotFoundError:
        print("Error: The 'docker' command was not found. Is Docker installed and in your system PATH?",
              file=sys.stderr)
    except Exception as e:
        print(f" An unexpected error occurred: {str(e)}", file=sys.stderr)


# experiments/tasks.py
@shared_task
def run_db_script(experiment_id):
    #Get experiment and update its status.
    experiment = SparkExperiment.objects.select_related('script','dataset').get(id=experiment_id)
    experiment.status = 'Running'
    experiment.output = ""
    experiment.save()

    # Define the shared directory path.
    filename = f"experiment_{experiment.id}.{experiment.script.file_type}"
    tmp_path = os.path.join(SHARED_DIR, filename)

    try:
        # Write the script content directly to the shared volume
        with open(tmp_path, 'w' if experiment.script.file_type != 'jar' else 'wb') as f:
            f.write(experiment.script.content)

        # Update master to the service name and use the container path
        #TODO parameterize these constants
        cmd = ['spark-submit', '--master', 'spark://spark-master:7077', tmp_path]

        if experiment.script.file_type == 'jar' and experiment.script.main_class:
            cmd.extend(['--class', experiment.script.main_class])

        # Start process with piped output
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, # Merge stderr into stdout
            text=True
        )

        # 2. Optimized Logging (Buffer lines)
        log_buffer = []
        for line in iter(process.stdout.readline, ''):
            log_buffer.append(line)
            # Save every 20 lines to reduce DB load
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
        experiment.save()
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        copy_from_docker(SPARK_CONTAINER,
                         os.path.join(tmp_path,"results.txt"),
                         f"{experiment_id}_results.txt")
