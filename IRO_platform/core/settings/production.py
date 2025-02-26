# core/settings/production.py
import os
import dj_database_url
from .base import *

# Disable debug mode
DEBUG = False

# Set allowed hosts
ALLOWED_HOSTS = ['your-domain.com']  # Add your actual production domain(s)

# Security settings
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Database configuration
db_config = dj_database_url.config(
    default=os.getenv("DATABASE_URL"),
    conn_max_age=600,
)
db_config['ENGINE'] = 'django_tenants.postgresql_backend'

DATABASES = {
    'default': db_config
}

# Celery configuration
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL")

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}