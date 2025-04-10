# core/settings/base.py
import os
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'replace-this-with-a-real-secret-key'
DEBUG = False
ALLOWED_HOSTS = []

########################
# DJANGO-TENANTS SETUP #
########################

# The main django-tenants library
# Make sure you have installed django-tenants in your environment:
# pip install django-tenants

# We must split our apps into SHARED_APPS and TENANT_APPS.
# SHARED_APPS = apps common to all tenants, created in the public schema.
# TENANT_APPS = apps that will be created separately in each tenant schema.

SHARED_APPS = [
    'django_tenants',                  # mandatory for django-tenants
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Include the app that contains the Tenant and Domain models
    'tenants',
    'crispy_forms',
    'crispy_bootstrap5',
    'guardian',
    'rest_framework',
]

TENANT_APPS = [
    # These apps' models will be created in each tenant's individual schema:
    'apps.assessments',
    # Add additional tenant-specific apps here if needed
]

# The combination of SHARED_APPS and TENANT_APPS becomes the full INSTALLED_APPS:
INSTALLED_APPS = SHARED_APPS + TENANT_APPS

# The model that points to your tenant (public) table:
TENANT_MODEL = 'tenants.TenantConfig'     # app_label.ModelName
# The model that stores the domain -> tenant mapping:
TENANT_DOMAIN_MODEL = "tenants.TenantDomain"     # app_label.ModelName

# For Bootstrap 5 or another template pack, also install crispy-bootstrap5
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

DATABASE_ROUTERS = (
    'django_tenants.routers.TenantSyncRouter',
)

########################
# END DJANGO-TENANTS   #
########################

# core/settings/base.py - update MIDDLEWARE list

MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django_tenants.middleware.main.TenantMainMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',  # Authentication must run BEFORE our middleware
    'core.middleware.context_middleware.ContextMiddleware',     # Context middleware
    'core.middleware.logging_middleware.LoggingMiddleware',     # Add logging middleware
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
########################
# NEW: Guardian & Auth #
########################
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',             # default model backend
    'guardian.backends.ObjectPermissionBackend',             # enable object-level perms
]
ANONYMOUS_USER_NAME = "AnonymousUser"  # Guardian recommended setting

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ["templates"],
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

WSGI_APPLICATION = 'core.wsgi.application'

########################
# DATABASE CONFIG      #
########################
# Make sure you set the actual DB credentials in local/production overrides
# or environment variables. django-tenants uses the default DB connection,
# but the schema is adjusted per tenant request.

DATABASES = {
    'default': {
        'ENGINE': 'django_tenants.postgresql_backend',  # Changed from django.db.backends.postgresql
        'NAME': 'dma_db',
        'USER': 'dma_user',
        'PASSWORD': 'password',
        'HOST': 'db',
        'PORT': '5432',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR.parent, 'static'),
]
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Example Celery or other global settings can remain here
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')

########################
# LOGGING CONFIGURATION #
########################

# Create logs directory if it doesn't exist
LOG_DIR = os.path.join(BASE_DIR.parent, 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

# Get the current datetime for the log filename
log_datetime = datetime.now().strftime('%Y%m%d_%H%M%S')
LOG_FILENAME = f'app_{log_datetime}.log'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,

    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
            'style': '%', 
        },
        'simple': {
            'format': '%(levelname)s %(asctime)s %(message)s',
            'style': '%',
        },
        'tenant_aware': {
            'format': '%(levelname)s %(asctime)s %(module)s [TENANT:%(tenant)s] %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
            'style': '%',
            '()': 'core.middleware.logging_middleware.TenantFormatter',
        },
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, LOG_FILENAME),
            'formatter': 'verbose',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 10,
        },
        'tenant_file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, LOG_FILENAME),
            'formatter': 'tenant_aware',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 10,
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.server': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'tenant_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'tenants': {
            'handlers': ['console', 'tenant_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'frontend': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'core': {
            'handlers': ['console', 'tenant_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'apps.requests': {
            'handlers': ['console', 'tenant_file'],
            'level': 'INFO',
            'propagate': False,
        },
    }
}