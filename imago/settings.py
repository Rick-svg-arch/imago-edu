"""
Django settings for imago project.
"""

import os
import dj_database_url
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'una-clave-secreta-de-desarrollo-insegura')
DEBUG = os.getenv('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = [
    'imago-edu-1002890573313.us-central1.run.app',
    '.us-central1.run.app',
    '.run.app',
    '127.0.0.1',
    'localhost',
    '[::1]'
]

SERVICE_URL = os.getenv('SERVICE_URL')

CSRF_TRUSTED_ORIGINS = [
    'https://imago-edu-1002890573313.us-central1.run.app',
    'https://*.us-central1.run.app',
    'https://*.run.app',
]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'posts',
    'users.apps.UsersConfig',
    'lecturas',
    'storages',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

X_FRAME_OPTIONS = 'SAMEORIGIN'
ROOT_URLCONF = 'imago.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
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

WSGI_APPLICATION = 'imago.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'imago_prod',
        'USER': 'postgres',
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': '/cloudsql/imago-edu:us-central1:imago-db',
        'PORT': '5432',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'es-la'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True

# ====================
# CONFIGURACIÓN DE ARCHIVOS ESTÁTICOS Y MEDIA
# ====================

GS_BUCKET_NAME = os.getenv('GS_BUCKET_NAME')

print("\n" + "="*60)
print("CONFIGURACIÓN DE STORAGE")
print("="*60)

if GS_BUCKET_NAME:
    print(f"✓ Modo: GOOGLE CLOUD STORAGE")
    print(f"  Bucket: {GS_BUCKET_NAME}")
    
    # SOLO para archivos media usar Google Cloud Storage
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.gcloud.GoogleCloudStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }
    
    # Configuración de Google Cloud Storage (SOLO para media)
    GS_PROJECT_ID = 'imago-edu'
    GS_CREDENTIALS = None
    GS_FILE_OVERWRITE = False
    GS_MAX_MEMORY_SIZE = 10485760  # 10MB
    GS_QUERYSTRING_AUTH = False
    GS_LOCATION = ''
    
    # URL base para archivos media
    MEDIA_URL = f'https://storage.googleapis.com/{GS_BUCKET_NAME}/'
    
    print(f"  Media Backend: storages.backends.gcloud.GoogleCloudStorage")
    print(f"  Static Backend: whitenoise.storage.CompressedManifestStaticFilesStorage")
    print(f"  Project ID: {GS_PROJECT_ID}")
    print(f"  Media URL: {MEDIA_URL}")
    
else:
    print("✓ Modo: ALMACENAMIENTO LOCAL")
    
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }
    
    MEDIA_URL = '/media/'
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# CONFIGURACIÓN DE STATIC FILES (SIEMPRE REQUERIDA)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

print(f"  Static URL: {STATIC_URL}")
print(f"  Static Root: {STATIC_ROOT}")
print("="*60 + "\n")

# Configuración adicional
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_URL = "users:login"
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# LOGGING DETALLADO
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {name} - {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'storages': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'google.cloud': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'lecturas': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}