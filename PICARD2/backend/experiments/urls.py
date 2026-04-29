# experiments/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.list_experiments, name='list_experiments'),
    path('create/', views.create_experiment, name='create_experiment'),
    path('scripts/<int:script_id>/run/', views.run_script, name='run_script'),
    path('<int:experiment_id>/result/', views.download_experiment_result, name='download_experiment_result'),
    path('<int:experiment_id>/delete/', views.delete_experiment, name='delete_experiment'),
    path('<int:experiment_id>/', views.get_experiment_detail, name='get_experiment'),
    path('<int:experiment_id>/run/', views.run_experiment, name='run_experiment'),
]
