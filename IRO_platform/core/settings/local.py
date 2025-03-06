# core/settings/local.py
import os
import dj_database_url
from .base import *

# Enable DEBUG mode for local development
DEBUG = True

# Allow all hosts in local dev
ALLOWED_HOSTS = ["*"]

# 1) Parse connection info from DATABASE_URL (or default).
db_config = dj_database_url.config(
    default=os.getenv("DATABASE_URL", "postgres://postgres:password@localhost:5432/postgres"),
    conn_max_age=600,
)

# 2) Force the Django Tenants engine rather than the default Postgres engine
db_config['ENGINE'] = 'django_tenants.postgresql_backend'

DATABASES = {
    'default': db_config
}

# Disable password validators locally, for developer convenience
AUTH_PASSWORD_VALIDATORS = []

# Point Celery broker to Redis, or default to local Redis container
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")

# Override the log level in development to see more details
LOGGING['loggers']['django']['level'] = 'DEBUG'
LOGGING['loggers']['apps']['level'] = 'DEBUG'
LOGGING['loggers']['tenants']['level'] = 'DEBUG'
LOGGING['loggers']['frontend']['level'] = 'DEBUG'

# Also log to the console in development
for logger_name in LOGGING['loggers']:
    if 'console' not in LOGGING['loggers'][logger_name]['handlers']:
        LOGGING['loggers'][logger_name]['handlers'].append('console')