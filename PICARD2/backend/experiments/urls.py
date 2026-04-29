# experiments/urls.py
from django.urls import path
from . import views

urlpatterns = [
    #Get experiment(s)
    path('<int:experiment_id>/', views.get_experiment_detail, name='get_experiment'),
    path('', views.list_experiments, name='list_experiments'),
    #Create experiment
    path('create/<int:script_id>/<int:experiment_id>/', views.create_experiment, name='create_experiment'),
    #run an experiment
    path('run/<int:script_id>/scripts/', views.run_experiment, name='run_script'),
    path('run/<int:experiment_id>/experiments/', views.run_experiment, name='run_experiment'),
    #Cluster modification
    path('scale/', views.scale_spark_workers, name='scale_workers'),
]
