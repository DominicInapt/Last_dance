from django.urls import path
from . import views

urlpatterns = [
    # General listing
    path('experiments/', views.list_experiments, name='list_experiments'),
    # Execution & Viewing 
    path('experiments/create/', views.create_experiment, name='create_experiment'),
    path('experiment/<int:experiment_id>/', views.get_experiment_detail, name='get_experiment'),

    # The two execution endpoints we just updated:
    path('scripts/<int:script_id>/run/', views.run_script, name='run_script'),
    path('experiments/<int:experiment_id>/run/', views.run_experiment, name='run_experiment'), 
]