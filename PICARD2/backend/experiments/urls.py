# experiments/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('scripts/', views.list_scripts, name='list_scripts'),
    path('scripts/<int:experiment_id>/', views.get_experiment_detail, name='get_experiment'),
    path('scripts/upload/', views.upload_script, name='upload_script'),
    path('scripts/<int:experiment_id>/run/', views.run_experiment, name='run_script'),
]
