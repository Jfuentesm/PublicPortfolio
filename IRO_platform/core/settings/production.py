# core/settings/production.py
import os
import dj_database_url
import datetime  # Add this import
from .base import *

# Define APP_RUN_TIMESTAMP for unique log file names
APP_RUN_TIMESTAMP = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

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

# Production logging
# Adjust log paths for production environment
log_dir = os.getenv('LOG_DIR', '/var/log/dma')
os.makedirs(log_dir, exist_ok=True)

# Update log file locations for production - now using the defined APP_RUN_TIMESTAMP
LOGGING['handlers']['file_backend']['filename'] = os.path.join(log_dir, f'backend_{APP_RUN_TIMESTAMP}.log')
LOGGING['handlers']['file_frontend']['filename'] = os.path.join(log_dir, f'frontend_{APP_RUN_TIMESTAMP}.log')

# Increase max log file size
LOGGING['handlers']['file_backend']['maxBytes'] = 1024*1024*50  # 50 MB
LOGGING['handlers']['file_frontend']['maxBytes'] = 1024*1024*50  # 50 MB

# Add email handler for errors in production
LOGGING['handlers']['mail_admins'] = {
    'level': 'ERROR',
    'filters': ['require_debug_false'],
    'class': 'django.utils.log.AdminEmailHandler',
    'include_html': True,
}

LOGGING['loggers']['django']['handlers'].append('mail_admins')