# datasets/models.py
import uuid
from django.db import models
from django.contrib.auth.models import User

# Access levels
PRIVATE = 'private'
PUBLIC = 'public'

def dataset_file_path(instance, filename):
    # Saves exactly to: <MEDIA_ROOT>/files/datasets/<UUID>.csv
    return f'files/datasets/{instance.id}.csv'

class CSVDataset(models.Model):
    ACCESS_CHOICES = [
        (PRIVATE, 'Private'),
        (PUBLIC, 'Public'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='datasets')
    name = models.CharField(max_length=255, default="Unnamed Dataset")
    access_level = models.CharField(max_length=10, choices=ACCESS_CHOICES, default=PRIVATE)

    file = models.FileField(upload_to=dataset_file_path)

    uploaded_at = models.DateTimeField(auto_now_add=True)

    def get_absolute_file_path(self):
        # Django natively knows the absolute path on your backend server
        if self.file:
            return self.file.path
        return None

    def __str__(self):
        return f"{self.name} ({self.user.username})"