# experiments/models.py
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

class Product(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    sku = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

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
    access_modifier = models.CharField(
        max_length=10,
        choices=ACCESS_CHOICES,
        default=PRIVATE
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    # helper method so you can easily retrieve the path
    def get_file_path(self):
        return f"data/{self.id}.csv"

    def __str__(self):
        return f"Dataset {self.id} ({self.user.username})"

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
