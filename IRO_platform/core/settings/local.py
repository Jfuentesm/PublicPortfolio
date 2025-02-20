# core/settings/local.py
import os
import dj_database_url
from .base import *

# Enable DEBUG mode for local development
DEBUG = True

# Allow all hosts in local dev
ALLOWED_HOSTS = ["*"]

# Database configuration:
# Read from DATABASE_URL if set; otherwise fall back to a localhost connection
DATABASES = {
    'default': dj_database_url.config(
        default=os.getenv("DATABASE_URL", "postgres://postgres:password@localhost:5432/postgres"),
        conn_max_age=600,
    )
}

# Disable password validators locally for faster dev iteration
AUTH_PASSWORD_VALIDATORS = []

# Point Celery broker to Redis via environment variable or default to local Redis container
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")

# Optionally adjust any additional local-only Django settings or logging here.