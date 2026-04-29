from django.urls import path
from . import views


urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('user_login/', views.user_login, name='user_login'),
    path('session/', views.auth_session, name='auth_session'),
    path('logout/', views.auth_logout, name='auth_logout'),
    path('github/login/', views.github_login, name='github_login'),
    path('github/callback/', views.github_callback, name='github_callback'),
]