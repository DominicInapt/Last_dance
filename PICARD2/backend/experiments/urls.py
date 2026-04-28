from django.urls import path
from . import views

urlpatterns = [
    # General listing
    path('scripts/', views.list_scripts, name='list_scripts'),
    path('experiments/', views.list_experiments, name='list_experiments'),

    # Auth
    path('signup/', views.signup, name='signup'),
    path('user_login/', views.user_login, name='user_login'),

    # Uploads
    path('upload/script/', views.upload_script, name='upload_script'),
    path('upload/csv/', views.upload_csv, name='upload_csv'),

    # Execution & Viewing 
    path('experiments/create/', views.create_experiment, name='create_experiment'),
    path('experiment/<int:experiment_id>/', views.get_experiment_detail, name='get_experiment'),

    # The two execution endpoints we just updated:
    path('scripts/<int:script_id>/run/', views.run_script, name='run_script'),
    path('experiments/<int:experiment_id>/run/', views.run_experiment, name='run_experiment'), 
]