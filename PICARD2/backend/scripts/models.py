# datasets/models.py
from django.db import models
from django.contrib.auth.models import User

# Access levels
PRIVATE = 'private'
PUBLIC = 'public'


class Script(models.Model):
    # Types
    PYTHON = 'py'
    JAR = 'jar'

    TYPE_CHOICES = [(PYTHON, 'Python Script'), (JAR,'Java/Scala JAR')]
    ACCESS_CHOICES = [
        (PRIVATE, 'Private'),
        (PUBLIC, 'Public'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=3, choices=TYPE_CHOICES, default=PYTHON)
    content = models.BinaryField()
    # Defaults to 'private'
    access_level = models.CharField(
        max_length=10,
        choices=ACCESS_CHOICES,
        default=PRIVATE
    )
    main_class = models.CharField(max_length=255, blank=True,null=True, help_text='e.g., com.example.SparkJob')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.access_level})"