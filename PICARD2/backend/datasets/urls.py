from django.urls import path
from . import views


urlpatterns = [
    path('upload/csv/', views.upload_csv, name='upload_csv'),
    path('list/', views.list_datasets, name='list_datasets')
]