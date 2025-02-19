import os
import dj_database_url
from .base import *

# In local development we usually want DEBUG = True
DEBUG = True

# If running in Docker, often we simply allow all hosts or set your domain
ALLOWED_HOSTS = ["*"]

# Use the environment variable if set, or fallback
DATABASES = {
    'default': dj_database_url.config(
        default='postgres://postgres:password@localhost:5432/postgres',
        conn_max_age=600,
    )
}

# For local dev, we typically turn off password validation
AUTH_PASSWORD_VALIDATORS = []

# Optionally other local dev settings...
# e.g. emailing to console, logging, etc.