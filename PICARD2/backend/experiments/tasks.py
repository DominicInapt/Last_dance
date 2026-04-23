# experiments/tasks.py
import subprocess
import tempfile
import os
from celery import shared_task
from .models import SparkExperiment, Script

SHARED_DIR = os.environ.get('SPARK_SHARED_DIR', '/opt/bitnami/spark')

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