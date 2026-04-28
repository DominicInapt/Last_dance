# datasets/models.py
from django.db import models
from django.contrib.auth.models import User

# Access levels
PRIVATE = 'private'
PUBLIC = 'public'

class CSVDataset(models.Model):
    ACCESS_CHOICES = [
        (PRIVATE, 'Private'),
        (PUBLIC, 'Public'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='datasets'
    )

    name = models.CharField(max_length=255, default="Unnamed Dataset")

    access_level = models.CharField(
        max_length=10,
        choices=ACCESS_CHOICES,
        default=PRIVATE
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    # helper method so you can easily retrieve the path
    def get_file_path(self):
        return f"data/{self.id}.csv"

    def __str__(self):
        return f"{self.name} ({self.user.username})"