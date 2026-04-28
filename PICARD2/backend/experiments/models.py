# experiments/models.py
from django.db import models
from django.contrib.auth.models import User

from datasets.models import CSVDataset
from scripts.models import Script

# Access levels
PRIVATE = 'private'
PUBLIC = 'public'


class SparkExperiment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    script = models.ForeignKey(Script, on_delete=models.CASCADE, related_name='runs')
    dataset = models.ForeignKey(CSVDataset, on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(max_length=20, default='Pending')
    output = models.TextField(default="") # Stores the live logs
    created_at = models.DateTimeField(auto_now_add=True)

    def get_results_path(self):
        return f"results/{self.id}.txt"

    def __str__(self):
        return f"Experiment {self.id} ({self.status})"
