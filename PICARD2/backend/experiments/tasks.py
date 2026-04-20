# experiments/tasks.py
import subprocess
import tempfile
import os
from celery import shared_task
from .models import SparkExperiment, Script


@shared_task
# experiments/tasks.py
@shared_task
def run_db_script(experiment_id):
    #Get experiment and update its status.
    experiment = SparkExperiment.objects.select_related('script','dataset').get(id=experiment_id)
    experiment.status = 'Running'
    experiment.output = ""
    experiment.save()

    with tempfile.NamedTemporaryFile(suffix=f".{experiment.script.file_type}", delete=False) as tmp:
        #Grab script from the relate db
        tmp.write(experiment.script.content)
        tmp_path = tmp.name

    try:
        #Appends a main-class argument if its a jar
        cmd = ['spark-submit', '--master', 'local[*]', tmp_path]

        if experiment.script.file_type == 'jar' and experiment.script.main_class:
            cmd.extend(['--class', experiment.script.main_class])

        # Start process with piped output
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, # Merge stderr into stdout
            text=True
        )

        # Read line by line as it happens
        for line in iter(process.stdout.readline, ''):
            experiment.output += line
            experiment.save(update_fields=['output']) # Optimized update

        process.wait()
        experiment.status = 'Success' if process.returncode == 0 else 'Failed'
    except Exception as e:
        experiment.output += f"\nInternal Error: {str(e)}"
        experiment.status = 'Failed'
    finally:
        experiment.save()
        if os.path.exists(tmp_path):
            os.remove(tmp_path)