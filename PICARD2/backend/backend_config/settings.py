import os
from pathlib import Path

from django.conf.global_settings import STATIC_URL

#TODO change in production
DEBUG = True
SECRET_KEY = 'django-insecure-this-is-just-for-local-testing-change-in-prod'

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST', 'db'), # Matches the service name in docker-compose
        'PORT': os.environ.get('DB_PORT', '3306'),
    }
}
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://redis:6379/0")

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# Media files (User-uploaded datasets, scripts, etc.)
MEDIA_URL = '/media/'
STATIC_URL = '/static/'
ROOT_URLCONF = 'backend_config.urls'


# Point the MEDIA_ROOT to the shared Docker volume.
# We use a fallback to a local 'media' folder so it doesn't crash if run outside Docker.
MEDIA_ROOT = os.environ.get('SPARK_SHARED_DIR', os.path.join(BASE_DIR, 'media'))
INSTALLED_APPS = [
    # 1. Default Django apps (Core functionality)
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',  # <-- This specifically fixes your current error!
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # 2. Third-party apps
    'rest_framework',               # <-- Required for your serializers and JsonResponse

    # 3. Your local apps
    'experiments',                  # <-- Tells Django where to find your models and views
    'authentication',
    'datasets',
    'scripts'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware', # Manages user sessions
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware', # Manages user logins
    'django.contrib.messages.middleware.MessageMiddleware', # Manages popup alerts
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [], # You can add custom template directories here later if needed
        'APP_DIRS': True, # Tells Django to look inside INSTALLED_APPS for templates
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
#xd
