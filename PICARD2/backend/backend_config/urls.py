# your_project_name/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # This connects your project to the experiments app URLs!
    path('experiments/', include('experiments.urls')),
    path('scripts/', include('scripts.urls')),
    path('datasets/', include('datasets.urls')),
    path('auth/', include('authentication.urls'))
]