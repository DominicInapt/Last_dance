# experiments/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('scripts/', views.list_scripts, name='list_scripts'),
    path('experiment/<int:experiment_id>/', views.get_experiment_detail, name='get_experiment'),

    path('signup/', views.signup, name='signup'),
    path('user_login/', views.user_login, name='user_login'),

    path('upload/script/', views.upload_script, name='upload_script'),
    path('scripts/<int:experiment_id>/run/', views.run_experiment, name='run_script'),
    path('upload/csv/', views.upload_csv, name='upload_csv'),
]
