# datasets/models.py
import os

from django.db import models
from django.contrib.auth.models import User

# Access levels
PRIVATE = 'private'
PUBLIC = 'public'

# The only service using the datasets is the spark cluster so it makes some sense to store them there.
SHARED_DIR = os.environ.get('SPARK_SHARED_DIR', '/opt/spark/apps')

class CSVDataset(models.Model):
    ACCESS_CHOICES = [
        (PRIVATE, 'Private'),
        (PUBLIC, 'Public'),
    ]

    user = models.ForeignKey(User,on_delete=models.CASCADE,related_name='datasets')
    name = models.CharField(max_length=255, default="Unnamed Dataset")
    access_level = models.CharField(max_length=10, choices=ACCESS_CHOICES, default=PRIVATE)

    # NEW: Django's native FileField handles the saving and chunking automatically
    file = models.FileField(upload_to='data/')

    uploaded_at = models.DateTimeField(auto_now_add=True)

    # helper method so you can easily retrieve the path
    def get_file_path(self):
        # Save into a 'data' subfolder inside the shared Spark volume
        return os.path.join(SHARED_DIR, "data", f"{self.id}.csv")

    def __str__(self):
        return f"{self.name} ({self.user.username})"