# your_project_name/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # This connects your project to the experiments app URLs!
    path('', include('experiments.urls'))
]