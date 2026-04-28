from django.urls import path
from . import views


urlpatterns = [
    path('upload/script/', views.upload_script, name='upload_script'),
    path('scripts/', views.list_scripts, name='list_scripts'),
]