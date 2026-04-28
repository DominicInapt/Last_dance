from django.urls import path
from . import views

urlpatterns = [
    # General listing
    path('', views.list_experiments, name='list_experiments'),
    # Execution & Viewing 
    path('create/', views.create_experiment, name='create_experiment'),
    path('<int:experiment_id>/', views.get_experiment_detail, name='get_experiment'),

    # The two execution endpoints we just updated:
    path('<int:script_id>/run_script/', views.run_script, name='run_script'),
    path('<int:experiment_id>/run_experiment/', views.run_experiment, name='run_experiment'),
]