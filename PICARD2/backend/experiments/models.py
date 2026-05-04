# experiments/models.py
import os
import uuid

from django.conf import settings
from django.db import models
from django.contrib.auth.models import User

from datasets.models import CSVDataset
from scripts.models import Script

# Access levels
PRIVATE = 'private'
PUBLIC = 'public'

def experiment_output_path(instance, filename):
    # Saves exactly to: <MEDIA_ROOT>/files/output/<UUID>.txt
    return f'files/output/{instance.id}.txt'

# NEW: Dynamic path generator for the results
def experiment_result_path(instance, filename):
    return f'files/results/{instance.id}.txt'

class SparkExperiment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    script = models.ForeignKey(Script, on_delete=models.CASCADE, related_name='runs')
    dataset = models.ForeignKey(CSVDataset, on_delete=models.CASCADE, null=True, blank=True)
    #specific details on experiment.
    status = models.CharField(max_length=20, default='Pending')
    args = models.TextField(default='')
    #input output
    output = models.FileField(upload_to=experiment_output_path, null=True, blank=True)
    result = models.FileField(upload_to=experiment_result_path, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def get_results_path(self):
        return f"results/{self.id}.txt"

    def __str__(self):
        return f"Experiment {self.id} ({self.status})"

    def get_absolute_output_path(self):
        if self.output and hasattr(self.output, 'path'):
            return self.output.path
        # Fallback if the file object isn't fully bound yet
        return os.path.join(settings.MEDIA_ROOT, 'files', 'output', f'{self.id}.txt')

    def get_absolute_result_path(self):
        if self.result and hasattr(self.result, 'path'):
            return self.result.path
        return os.path.join(settings.MEDIA_ROOT, 'files', 'results', f'{self.id}.txt')