<goal>


</goal>


<output instruction>
1) Explain 
2) Give me the COMPLETE UPDATED VERSION of each script that needs to be updated
</output instruction>



 <Tree of Included Files>
- compose.yaml
- Dockerfile
- Dockerfile
- compose.yaml
- core/__init__.py
- core/celery.py
- core/settings/__init__.py
- core/settings/base.py
- core/settings/local.py
- core/urls.py
- core/wsgi.py
- init-scripts/01-init-schemas.sql
- manage.py
- requirements.txt
- schema_solve_prompt.md




 <Tree of Included Files>


<Concatenated Source Code>

<file path='compose.yaml'>
services:
  web:
    build: .
    command: >
      sh -c "
        echo 'Checking for database availability...' &&
        until pg_isready -h db -p 5432 -U dma_user; do 
          echo '[$(date)] Still waiting for database to be ready...'; 
          sleep 2; 
        done && 
        echo 'Database is ready!' &&
        python manage.py migrate &&
        gunicorn core.wsgi:application --bind 0.0.0.0:8000 --access-logfile - --error-logfile -"
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    environment:
      - DJANGO_SETTINGS_MODULE=core.settings.local
      - DATABASE_URL=postgres://dma_user:password@db:5432/dma_db
      - PYTHONUNBUFFERED=1
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  db:
    image: postgres:14
    restart: always
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d
    environment:
      POSTGRES_USER: dma_user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: dma_db
      POSTGRES_INITDB_ARGS: "--auth-host=scram-sha-256"
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U dma_user -d dma_db"]
      interval: 5s
      timeout: 5s
      retries: 5
      start_period: 10s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  redis:
    image: redis:7
    restart: always
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  worker:
    build: .
    command: celery -A core worker --loglevel=info
    volumes:
      - .:/app
    environment:
      - DJANGO_SETTINGS_MODULE=core.settings.local
      - DATABASE_URL=postgres://dma_user:password@db:5432/dma_db
      - CELERY_BROKER_URL=redis://redis:6379/0
      - PYTHONUNBUFFERED=1
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

volumes:
  postgres_data:
</file>

<file path='Dockerfile'>
# Dockerfile
# Use a slim Python base image
FROM python:3.11-slim

# Prevent Python from writing pyc files or buffering stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies including postgresql-client
RUN apt-get update \
    && apt-get install -y postgresql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . /app/

# Default command (Docker Compose will typically override this)
CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000"]
</file>

<file path='Dockerfile'>
# Dockerfile
# Use a slim Python base image
FROM python:3.11-slim

# Prevent Python from writing pyc files or buffering stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies including postgresql-client
RUN apt-get update \
    && apt-get install -y postgresql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . /app/

# Default command (Docker Compose will typically override this)
CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000"]
</file>

<file path='compose.yaml'>
services:
  web:
    build: .
    command: >
      sh -c "
        echo 'Checking for database availability...' &&
        until pg_isready -h db -p 5432 -U dma_user; do 
          echo '[$(date)] Still waiting for database to be ready...'; 
          sleep 2; 
        done && 
        echo 'Database is ready!' &&
        python manage.py migrate &&
        gunicorn core.wsgi:application --bind 0.0.0.0:8000 --access-logfile - --error-logfile -"
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    environment:
      - DJANGO_SETTINGS_MODULE=core.settings.local
      - DATABASE_URL=postgres://dma_user:password@db:5432/dma_db
      - PYTHONUNBUFFERED=1
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  db:
    image: postgres:14
    restart: always
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d
    environment:
      POSTGRES_USER: dma_user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: dma_db
      POSTGRES_INITDB_ARGS: "--auth-host=scram-sha-256"
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U dma_user -d dma_db"]
      interval: 5s
      timeout: 5s
      retries: 5
      start_period: 10s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  redis:
    image: redis:7
    restart: always
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  worker:
    build: .
    command: celery -A core worker --loglevel=info
    volumes:
      - .:/app
    environment:
      - DJANGO_SETTINGS_MODULE=core.settings.local
      - DATABASE_URL=postgres://dma_user:password@db:5432/dma_db
      - CELERY_BROKER_URL=redis://redis:6379/0
      - PYTHONUNBUFFERED=1
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

volumes:
  postgres_data:
</file>

<file path='core/__init__.py'>

</file>

<file path='core/celery.py'>
# core/celery.py
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.local')

app = Celery('core')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

</file>

<file path='core/settings/__init__.py'>
# This file is intentionally empty (or can be left out if not needed).
# It just tells Python that 'settings' is a package.
</file>

<file path='core/settings/base.py'>
# core/settings/base.py
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'replace-this-with-a-real-secret-key'
DEBUG = False
ALLOWED_HOSTS = []

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Add additional apps as needed, e.g. 'myapp',
]

MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            # os.path.join(BASE_DIR, 'templates'),
        ],
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

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
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

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Celery (common config)
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')

</file>

<file path='core/settings/local.py'>
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
</file>

<file path='core/urls.py'>
# core/urls.py
from django.contrib import admin
from django.http import HttpResponse
from django.urls import path

def home(request):
    return HttpResponse("Welcome to the IRO Platform!")

urlpatterns = [
    path('', home, name='home'),
    path('admin/', admin.site.urls),
]
</file>

<file path='core/wsgi.py'>
# core/wsgi.py
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.local')

application = get_wsgi_application()

</file>

<file path='init-scripts/01-init-schemas.sql'>
--
-- 01-init-schemas.sql
--

-- Create the public tenant_config table
CREATE TABLE IF NOT EXISTS public.tenant_config (
    tenant_id SERIAL PRIMARY KEY,
    tenant_name VARCHAR(100) NOT NULL UNIQUE,
    created_on TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Define the create_tenant_schema function
CREATE OR REPLACE FUNCTION create_tenant_schema(tenant_name TEXT) RETURNS void AS $$
DECLARE
    schema_name TEXT := 'tenant_' || tenant_name;
BEGIN
    -- 1) Create the tenant schema if it doesn’t exist
    EXECUTE format('CREATE SCHEMA IF NOT EXISTS %I', schema_name);

    ---------------------------------------------------------------------------
    -- 2) IRO
    ---------------------------------------------------------------------------
    EXECUTE format($f$
        CREATE TABLE IF NOT EXISTS %I.iro (
            iro_id SERIAL PRIMARY KEY,
            tenant_id INT NOT NULL,
            current_version_id INT,
            current_stage VARCHAR(50) NOT NULL DEFAULT 'Draft',
            type VARCHAR(20) NOT NULL,
            source_of_iro VARCHAR(255),
            esrs_standard VARCHAR(100),
            last_assessment_date TIMESTAMP,
            assessment_count INT DEFAULT 0,
            last_assessment_score NUMERIC(5,2),
            created_on TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_on TIMESTAMP NOT NULL DEFAULT NOW(),
            CONSTRAINT iro_tenant_fk
                FOREIGN KEY (tenant_id)
                REFERENCES public.tenant_config(tenant_id)
                ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_iro_tenant_id     ON %I.iro (tenant_id);
        CREATE INDEX IF NOT EXISTS idx_iro_stage         ON %I.iro (current_stage);
        CREATE INDEX IF NOT EXISTS idx_iro_esrs_standard ON %I.iro (esrs_standard);
    $f$, schema_name, schema_name, schema_name, schema_name);

    ---------------------------------------------------------------------------
    -- 3) IRO_Version (Corrected: 5 %I placeholders, 5 arguments)
    ---------------------------------------------------------------------------
    EXECUTE format($f$
        CREATE TABLE IF NOT EXISTS %I.iro_version (
            version_id SERIAL PRIMARY KEY,
            iro_id INT NOT NULL,
            tenant_id INT NOT NULL,
            version_number INT NOT NULL,
            title VARCHAR(255) NOT NULL,
            description TEXT NOT NULL,
            sust_topic_level1 VARCHAR(100),
            sust_topic_level2 VARCHAR(100),
            sust_topic_level3 VARCHAR(100),
            value_chain_lv1 VARCHAR[] DEFAULT '{}',
            value_chain_lv2 VARCHAR[] DEFAULT '{}',
            economic_activity VARCHAR[] DEFAULT '{}',
            status VARCHAR(50) NOT NULL DEFAULT 'Draft',
            created_by INT NOT NULL,
            created_on TIMESTAMP NOT NULL DEFAULT NOW(),
            parent_version_id INT,
            split_type VARCHAR(50),
            CONSTRAINT fk_iro
                FOREIGN KEY (iro_id)
                REFERENCES %I.iro(iro_id)
                ON DELETE CASCADE,
            CONSTRAINT fk_tenant
                FOREIGN KEY (tenant_id)
                REFERENCES public.tenant_config(tenant_id)
                ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_iro_version_iro_id    ON %I.iro_version (iro_id);
        CREATE INDEX IF NOT EXISTS idx_iro_version_tenant_id ON %I.iro_version (tenant_id);
        CREATE INDEX IF NOT EXISTS idx_iro_version_status    ON %I.iro_version (status);
    $f$, schema_name, schema_name, schema_name, schema_name, schema_name);

    ---------------------------------------------------------------------------
    -- 4) IRO_Relationship
    ---------------------------------------------------------------------------
    EXECUTE format($f$
        CREATE TABLE IF NOT EXISTS %I.iro_relationship (
            relationship_id SERIAL PRIMARY KEY,
            tenant_id INT NOT NULL,
            source_iro_id INT NOT NULL,
            target_iro_id INT NOT NULL,
            relationship_type VARCHAR(50) NOT NULL,
            created_on TIMESTAMP NOT NULL DEFAULT NOW(),
            created_by INT NOT NULL,
            notes TEXT,
            CONSTRAINT fk_tenant
                FOREIGN KEY (tenant_id)
                REFERENCES public.tenant_config(tenant_id)
                ON DELETE CASCADE,
            CONSTRAINT fk_source_iro
                FOREIGN KEY (source_iro_id)
                REFERENCES %I.iro(iro_id),
            CONSTRAINT fk_target_iro
                FOREIGN KEY (target_iro_id)
                REFERENCES %I.iro(iro_id)
        );
        CREATE INDEX IF NOT EXISTS idx_iro_relationship_tenant_id ON %I.iro_relationship (tenant_id);
        CREATE INDEX IF NOT EXISTS idx_iro_relationship_src_tgt   ON %I.iro_relationship (source_iro_id, target_iro_id);
    $f$, schema_name, schema_name, schema_name, schema_name, schema_name);

    ---------------------------------------------------------------------------
    -- 5) impact_assessment
    ---------------------------------------------------------------------------
    EXECUTE format($f$
        CREATE TABLE IF NOT EXISTS %I.impact_assessment (
            impact_assessment_id SERIAL PRIMARY KEY,
            iro_id INT NOT NULL,
            tenant_id INT NOT NULL,
            impact_materiality_def_version_id INT,
            time_horizon VARCHAR(20) NOT NULL,
            actual_or_potential VARCHAR(50),
            related_to_human_rights VARCHAR(50),
            scale_score INT CHECK (scale_score BETWEEN 1 AND 5),
            scale_rationale TEXT,
            scope_score INT CHECK (scope_score BETWEEN 1 AND 5),
            scope_rationale TEXT,
            irremediability_score INT CHECK (irremediability_score BETWEEN 1 AND 5),
            irremediability_rationale TEXT,
            likelihood_score INT CHECK (likelihood_score BETWEEN 1 AND 5),
            likelihood_rationale TEXT,
            severity_score NUMERIC(5,2),
            impact_materiality_score NUMERIC(5,2),
            overall_rationale TEXT,
            related_documents TEXT,
            created_on TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_on TIMESTAMP NOT NULL DEFAULT NOW(),
            CONSTRAINT fk_impact_iro
                FOREIGN KEY (iro_id)
                REFERENCES %I.iro(iro_id)
                ON DELETE CASCADE,
            CONSTRAINT fk_impact_tenant
                FOREIGN KEY (tenant_id)
                REFERENCES public.tenant_config(tenant_id)
                ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_impact_assessment_tenant_id ON %I.impact_assessment (tenant_id);
        CREATE INDEX IF NOT EXISTS idx_impact_assessment_iro_id    ON %I.impact_assessment (iro_id);
    $f$, schema_name, schema_name, schema_name, schema_name);

    ---------------------------------------------------------------------------
    -- 6) risk_opp_assessment
    ---------------------------------------------------------------------------
    EXECUTE format($f$
        CREATE TABLE IF NOT EXISTS %I.risk_opp_assessment (
            risk_opp_assessment_id SERIAL PRIMARY KEY,
            iro_id INT NOT NULL,
            tenant_id INT NOT NULL,
            fin_materiality_def_version_id INT,
            time_horizon VARCHAR(20) NOT NULL,
            workforce_risk INT CHECK (workforce_risk BETWEEN 1 AND 5),
            workforce_risk_rationale TEXT,
            operational_risk INT CHECK (operational_risk BETWEEN 1 AND 5),
            operational_risk_rationale TEXT,
            cost_of_capital_risk INT CHECK (cost_of_capital_risk BETWEEN 1 AND 5),
            cost_of_capital_risk_rationale TEXT,
            reputational_risk INT CHECK (reputational_risk BETWEEN 1 AND 5),
            reputational_risk_rationale TEXT,
            legal_compliance_risk INT CHECK (legal_compliance_risk BETWEEN 1 AND 5),
            legal_compliance_risk_rationale TEXT,
            likelihood_score INT CHECK (likelihood_score BETWEEN 1 AND 5),
            likelihood_rationale TEXT,
            financial_magnitude_score NUMERIC(5,2),
            financial_materiality_score NUMERIC(5,2),
            overall_rationale TEXT,
            related_documents TEXT,
            created_on TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_on TIMESTAMP NOT NULL DEFAULT NOW(),
            CONSTRAINT fk_risk_opp_iro
                FOREIGN KEY (iro_id)
                REFERENCES %I.iro(iro_id)
                ON DELETE CASCADE,
            CONSTRAINT fk_risk_opp_tenant
                FOREIGN KEY (tenant_id)
                REFERENCES public.tenant_config(tenant_id)
                ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_risk_opp_assessment_tenant_id ON %I.risk_opp_assessment (tenant_id);
        CREATE INDEX IF NOT EXISTS idx_risk_opp_assessment_iro_id    ON %I.risk_opp_assessment (iro_id);
    $f$, schema_name, schema_name, schema_name, schema_name);

    ---------------------------------------------------------------------------
    -- 7) review
    ---------------------------------------------------------------------------
    EXECUTE format($f$
        CREATE TABLE IF NOT EXISTS %I.review (
            review_id SERIAL PRIMARY KEY,
            iro_id INT NOT NULL,
            tenant_id INT NOT NULL,
            iro_version_id INT,
            reviewer_id INT NOT NULL,
            status VARCHAR(50) NOT NULL DEFAULT 'Draft',
            notes TEXT NOT NULL DEFAULT '',
            created_on TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_on TIMESTAMP NOT NULL DEFAULT NOW(),
            CONSTRAINT review_iro_fk
                FOREIGN KEY (iro_id)
                REFERENCES %I.iro(iro_id)
                ON DELETE CASCADE,
            CONSTRAINT review_tenant_fk
                FOREIGN KEY (tenant_id)
                REFERENCES public.tenant_config(tenant_id)
                ON DELETE CASCADE,
            CONSTRAINT review_version_fk
                FOREIGN KEY (iro_version_id)
                REFERENCES %I.iro_version(version_id)
                ON DELETE SET NULL
        );
        CREATE INDEX IF NOT EXISTS idx_review_tenant_id  ON %I.review (tenant_id);
        CREATE INDEX IF NOT EXISTS idx_review_iro_id     ON %I.review (iro_id);
        CREATE INDEX IF NOT EXISTS idx_review_version_id ON %I.review (iro_version_id);
        CREATE INDEX IF NOT EXISTS idx_review_status     ON %I.review (status);
    $f$, schema_name, schema_name, schema_name, schema_name, schema_name, schema_name, schema_name);

    ---------------------------------------------------------------------------
    -- 8) signoff
    ---------------------------------------------------------------------------
    EXECUTE format($f$
        CREATE TABLE IF NOT EXISTS %I.signoff (
            signoff_id SERIAL PRIMARY KEY,
            review_id INT NOT NULL,
            tenant_id INT NOT NULL,
            iro_version_id INT,
            signed_by INT NOT NULL,
            signed_on TIMESTAMP NOT NULL DEFAULT NOW(),
            signature_ref VARCHAR(255),
            comments TEXT NOT NULL DEFAULT '',
            CONSTRAINT signoff_review_fk
                FOREIGN KEY (review_id)
                REFERENCES %I.review(review_id)
                ON DELETE CASCADE,
            CONSTRAINT signoff_tenant_fk
                FOREIGN KEY (tenant_id)
                REFERENCES public.tenant_config(tenant_id)
                ON DELETE CASCADE,
            CONSTRAINT signoff_version_fk
                FOREIGN KEY (iro_version_id)
                REFERENCES %I.iro_version(version_id)
                ON DELETE SET NULL
        );
        CREATE INDEX IF NOT EXISTS idx_signoff_tenant_id ON %I.signoff (tenant_id);
        CREATE INDEX IF NOT EXISTS idx_signoff_review_id ON %I.signoff (review_id);
        CREATE INDEX IF NOT EXISTS idx_signoff_signed_by ON %I.signoff (signed_by);
    $f$, schema_name, schema_name, schema_name, schema_name, schema_name, schema_name);

    ---------------------------------------------------------------------------
    -- 9) audit_trail
    ---------------------------------------------------------------------------
    EXECUTE format($f$
        CREATE TABLE IF NOT EXISTS %I.audit_trail (
            audit_id SERIAL PRIMARY KEY,
            tenant_id INT NOT NULL,
            entity_type VARCHAR(50) NOT NULL,
            entity_id INT NOT NULL,
            action VARCHAR(50) NOT NULL,
            user_id INT NOT NULL,
            timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
            data_diff JSONB NOT NULL DEFAULT '{}',
            CONSTRAINT fk_audit_trail_tenant
                FOREIGN KEY (tenant_id)
                REFERENCES public.tenant_config(tenant_id)
                ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_audit_trail_tenant_id      ON %I.audit_trail (tenant_id);
        CREATE INDEX IF NOT EXISTS idx_audit_trail_entity_type_id ON %I.audit_trail (entity_type, entity_id);
        CREATE INDEX IF NOT EXISTS idx_audit_trail_timestamp      ON %I.audit_trail (timestamp);
    $f$, schema_name, schema_name, schema_name, schema_name);

    ---------------------------------------------------------------------------
    -- 10) AUXILIARY TABLES
    ---------------------------------------------------------------------------
    -- impact_materiality_def
    EXECUTE format($f$
        CREATE TABLE IF NOT EXISTS %I.impact_materiality_def (
            def_id SERIAL PRIMARY KEY,
            tenant_id INT NOT NULL,
            version_num INT NOT NULL,
            dimension VARCHAR(50) NOT NULL,
            score_value INT NOT NULL CHECK (score_value BETWEEN 1 AND 5),
            definition_text TEXT NOT NULL,
            valid_from TIMESTAMP NOT NULL,
            valid_to TIMESTAMP,
            created_on TIMESTAMP NOT NULL DEFAULT NOW(),
            created_by INT NOT NULL,
            CONSTRAINT fk_tenant_impact_def
                FOREIGN KEY (tenant_id)
                REFERENCES public.tenant_config(tenant_id)
                ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_imp_mat_def_tenant_id   ON %I.impact_materiality_def (tenant_id);
        CREATE INDEX IF NOT EXISTS idx_imp_mat_def_version_dim ON %I.impact_materiality_def (version_num, dimension);
    $f$, schema_name, schema_name, schema_name);

    -- fin_materiality_weights
    EXECUTE format($f$
        CREATE TABLE IF NOT EXISTS %I.fin_materiality_weights (
            weight_id SERIAL PRIMARY KEY,
            tenant_id INT NOT NULL,
            version_num INT NOT NULL,
            dimension VARCHAR(50) NOT NULL,
            weight NUMERIC(5,2) NOT NULL,
            valid_from TIMESTAMP NOT NULL,
            valid_to TIMESTAMP,
            created_on TIMESTAMP NOT NULL DEFAULT NOW(),
            created_by INT NOT NULL,
            CONSTRAINT fk_tenant_fin_weights
                FOREIGN KEY (tenant_id)
                REFERENCES public.tenant_config(tenant_id)
                ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_fin_weights_tenant_id   ON %I.fin_materiality_weights (tenant_id);
        CREATE INDEX IF NOT EXISTS idx_fin_weights_version_dim ON %I.fin_materiality_weights (version_num, dimension);
    $f$, schema_name, schema_name, schema_name);

    -- fin_materiality_magnitude_def
    EXECUTE format($f$
        CREATE TABLE IF NOT EXISTS %I.fin_materiality_magnitude_def (
            def_id SERIAL PRIMARY KEY,
            tenant_id INT NOT NULL,
            version_num INT NOT NULL,
            score_value INT NOT NULL CHECK (score_value BETWEEN 1 AND 5),
            definition_text TEXT NOT NULL,
            valid_from TIMESTAMP NOT NULL,
            valid_to TIMESTAMP,
            created_on TIMESTAMP NOT NULL DEFAULT NOW(),
            created_by INT NOT NULL,
            CONSTRAINT fk_tenant_fin_magnitude_def
                FOREIGN KEY (tenant_id)
                REFERENCES public.tenant_config(tenant_id)
                ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_fin_mag_def_tenant_id     ON %I.fin_materiality_magnitude_def (tenant_id);
        CREATE INDEX IF NOT EXISTS idx_fin_mag_def_version_score ON %I.fin_materiality_magnitude_def (version_num, score_value);
    $f$, schema_name, schema_name, schema_name);

END;
$$ LANGUAGE plpgsql;

-- Insert test tenants
INSERT INTO public.tenant_config (tenant_name) VALUES ('test1') ON CONFLICT DO NOTHING;
INSERT INTO public.tenant_config (tenant_name) VALUES ('test2') ON CONFLICT DO NOTHING;

-- Execute the function for test tenants
SELECT create_tenant_schema('test1');
SELECT create_tenant_schema('test2');
</file>

<file path='manage.py'>
#!/usr/bin/env python
import os
import sys

def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.local')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Make sure it's installed and "
            "available on your PYTHONPATH environment variable? "
            "Did you forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
</file>

<file path='requirements.txt'>
# requirements.txt
Django==4.2
gunicorn==20.1.0
psycopg2-binary==2.9.6
redis==4.5.5
celery==5.2.7
dj-database-url==0.5.0

</file>

<file path='schema_solve_prompt.md'>
<goal>
solve the error in schema creation shows below

</goal>


<output instruction>
1) Explain 
2) Give me the COMPLETE UPDATED VERSION of each script that needs to be updated
</output instruction>

<error>
db-1      | CREATE DATABASE
db-1      | 
db-1      | 
db-1      | /usr/local/bin/docker-entrypoint.sh: running /docker-entrypoint-initdb.d/01-init-schemas.sql
db-1      | CREATE TABLE
db-1      | CREATE FUNCTION
db-1      | INSERT 0 1
db-1      | INSERT 0 1
db-1      | 2025-02-19 16:20:30.643 UTC [62] ERROR:  too few arguments for format()
db-1      | 2025-02-19 16:20:30.643 UTC [62] CONTEXT:  PL/pgSQL function create_tenant_schema(text) line 38 at EXECUTE
db-1      | 2025-02-19 16:20:30.643 UTC [62] STATEMENT:  SELECT create_tenant_schema('test1');
db-1      | psql:/docker-entrypoint-initdb.d/01-init-schemas.sql:347: ERROR:  too few arguments for format()
db-1      | CONTEXT:  PL/pgSQL function create_tenant_schema(text) line 38 at EXECUTE
</error>

<init-scripts/01-init-schemas.sql>
--
-- 01-init-schemas.sql
--

CREATE TABLE IF NOT EXISTS public.tenant_config (
    tenant_id SERIAL PRIMARY KEY,
    tenant_name VARCHAR(100) NOT NULL UNIQUE,
    created_on TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE OR REPLACE FUNCTION create_tenant_schema(tenant_name TEXT) RETURNS void AS $$
DECLARE
    schema_name TEXT := format('tenant_%I', tenant_name);
BEGIN
    -- 1) Create the tenant schema if it doesn’t exist
    EXECUTE format('CREATE SCHEMA IF NOT EXISTS %s', schema_name);

    ---------------------------------------------------------------------------
    -- 2) IRO
    ---------------------------------------------------------------------------
    EXECUTE format($f$
        CREATE TABLE IF NOT EXISTS %I.iro (
            iro_id SERIAL PRIMARY KEY,
            tenant_id INT NOT NULL,
            current_version_id INT,
            current_stage VARCHAR(50) NOT NULL DEFAULT 'Draft',
            type VARCHAR(20) NOT NULL,
            source_of_iro VARCHAR(255),
            esrs_standard VARCHAR(100),
            last_assessment_date TIMESTAMP,
            assessment_count INT DEFAULT 0,
            last_assessment_score NUMERIC(5,2),
            created_on TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_on TIMESTAMP NOT NULL DEFAULT NOW(),
            CONSTRAINT iro_tenant_fk
              FOREIGN KEY (tenant_id)
              REFERENCES public.tenant_config(tenant_id)
              ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_iro_tenant_id     ON %I.iro (tenant_id);
        CREATE INDEX IF NOT EXISTS idx_iro_stage         ON %I.iro (current_stage);
        CREATE INDEX IF NOT EXISTS idx_iro_esrs_standard ON %I.iro (esrs_standard);
    $f$, schema_name, schema_name, schema_name, schema_name);

    ---------------------------------------------------------------------------
    -- 3) IRO_Version
    ---------------------------------------------------------------------------
    EXECUTE format($f$
        CREATE TABLE IF NOT EXISTS %I.iro_version (
            version_id SERIAL PRIMARY KEY,
            iro_id INT NOT NULL,
            tenant_id INT NOT NULL,
            version_number INT NOT NULL,
            title VARCHAR(255) NOT NULL,
            description TEXT NOT NULL,
            sust_topic_level1 VARCHAR(100),
            sust_topic_level2 VARCHAR(100),
            sust_topic_level3 VARCHAR(100),
            value_chain_lv1 VARCHAR[] DEFAULT '{}',
            value_chain_lv2 VARCHAR[] DEFAULT '{}',
            economic_activity VARCHAR[] DEFAULT '{}',
            status VARCHAR(50) NOT NULL DEFAULT 'Draft',
            created_by INT NOT NULL,
            created_on TIMESTAMP NOT NULL DEFAULT NOW(),
            parent_version_id INT,
            split_type VARCHAR(50),
            CONSTRAINT fk_iro
                FOREIGN KEY (iro_id)
                REFERENCES %I.iro(iro_id)
                ON DELETE CASCADE,
            CONSTRAINT fk_tenant
                FOREIGN KEY (tenant_id)
                REFERENCES public.tenant_config(tenant_id)
                ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_iro_version_iro_id    ON %I.iro_version (iro_id);
        CREATE INDEX IF NOT EXISTS idx_iro_version_tenant_id ON %I.iro_version (tenant_id);
        CREATE INDEX IF NOT EXISTS idx_iro_version_status    ON %I.iro_version (status);
    $f$, schema_name, schema_name, schema_name, schema_name);

    ---------------------------------------------------------------------------
    -- 4) IRO_Relationship
    ---------------------------------------------------------------------------
    EXECUTE format($f$
        CREATE TABLE IF NOT EXISTS %I.iro_relationship (
            relationship_id SERIAL PRIMARY KEY,
            tenant_id INT NOT NULL,
            source_iro_id INT NOT NULL,
            target_iro_id INT NOT NULL,
            relationship_type VARCHAR(50) NOT NULL,
            created_on TIMESTAMP NOT NULL DEFAULT NOW(),
            created_by INT NOT NULL,
            notes TEXT,
            CONSTRAINT fk_tenant
                FOREIGN KEY (tenant_id)
                REFERENCES public.tenant_config(tenant_id)
                ON DELETE CASCADE,
            CONSTRAINT fk_source_iro
                FOREIGN KEY (source_iro_id)
                REFERENCES %I.iro(iro_id),
            CONSTRAINT fk_target_iro
                FOREIGN KEY (target_iro_id)
                REFERENCES %I.iro(iro_id)
        );
        CREATE INDEX IF NOT EXISTS idx_iro_relationship_tenant_id ON %I.iro_relationship (tenant_id);
        CREATE INDEX IF NOT EXISTS idx_iro_relationship_src_tgt    ON %I.iro_relationship (source_iro_id, target_iro_id);
    $f$, schema_name, schema_name, schema_name, schema_name);

    ---------------------------------------------------------------------------
    -- 5) impact_assessment
    ---------------------------------------------------------------------------
    EXECUTE format($f$
        CREATE TABLE IF NOT EXISTS %I.impact_assessment (
            impact_assessment_id SERIAL PRIMARY KEY,
            iro_id INT NOT NULL,
            tenant_id INT NOT NULL,
            impact_materiality_def_version_id INT,
            time_horizon VARCHAR(20) NOT NULL,
            actual_or_potential VARCHAR(50),
            related_to_human_rights VARCHAR(50),
            scale_score INT CHECK (scale_score BETWEEN 1 AND 5),
            scale_rationale TEXT,
            scope_score INT CHECK (scope_score BETWEEN 1 AND 5),
            scope_rationale TEXT,
            irremediability_score INT CHECK (irremediability_score BETWEEN 1 AND 5),
            irremediability_rationale TEXT,
            likelihood_score INT CHECK (likelihood_score BETWEEN 1 AND 5),
            likelihood_rationale TEXT,
            severity_score NUMERIC(5,2),
            impact_materiality_score NUMERIC(5,2),
            overall_rationale TEXT,
            related_documents TEXT,
            created_on TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_on TIMESTAMP NOT NULL DEFAULT NOW(),
            CONSTRAINT fk_impact_iro
                FOREIGN KEY (iro_id)
                REFERENCES %I.iro(iro_id)
                ON DELETE CASCADE,
            CONSTRAINT fk_impact_tenant
                FOREIGN KEY (tenant_id)
                REFERENCES public.tenant_config(tenant_id)
                ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_impact_assessment_tenant_id ON %I.impact_assessment (tenant_id);
        CREATE INDEX IF NOT EXISTS idx_impact_assessment_iro_id    ON %I.impact_assessment (iro_id);
    $f$, schema_name, schema_name, schema_name, schema_name);

    ---------------------------------------------------------------------------
    -- 6) risk_opp_assessment
    ---------------------------------------------------------------------------
    EXECUTE format($f$
        CREATE TABLE IF NOT EXISTS %I.risk_opp_assessment (
            risk_opp_assessment_id SERIAL PRIMARY KEY,
            iro_id INT NOT NULL,
            tenant_id INT NOT NULL,
            fin_materiality_def_version_id INT,
            time_horizon VARCHAR(20) NOT NULL,
            workforce_risk INT CHECK (workforce_risk BETWEEN 1 AND 5),
            workforce_risk_rationale TEXT,
            operational_risk INT CHECK (operational_risk BETWEEN 1 AND 5),
            operational_risk_rationale TEXT,
            cost_of_capital_risk INT CHECK (cost_of_capital_risk BETWEEN 1 AND 5),
            cost_of_capital_risk_rationale TEXT,
            reputational_risk INT CHECK (reputational_risk BETWEEN 1 AND 5),
            reputational_risk_rationale TEXT,
            legal_compliance_risk INT CHECK (legal_compliance_risk BETWEEN 1 AND 5),
            legal_compliance_risk_rationale TEXT,
            likelihood_score INT CHECK (likelihood_score BETWEEN 1 AND 5),
            likelihood_rationale TEXT,
            financial_magnitude_score NUMERIC(5,2),
            financial_materiality_score NUMERIC(5,2),
            overall_rationale TEXT,
            related_documents TEXT,
            created_on TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_on TIMESTAMP NOT NULL DEFAULT NOW(),
            CONSTRAINT fk_risk_opp_iro
                FOREIGN KEY (iro_id)
                REFERENCES %I.iro(iro_id)
                ON DELETE CASCADE,
            CONSTRAINT fk_risk_opp_tenant
                FOREIGN KEY (tenant_id)
                REFERENCES public.tenant_config(tenant_id)
                ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_risk_opp_assessment_tenant_id ON %I.risk_opp_assessment (tenant_id);
        CREATE INDEX IF NOT EXISTS idx_risk_opp_assessment_iro_id    ON %I.risk_opp_assessment (iro_id);
    $f$, schema_name, schema_name, schema_name, schema_name);

    ---------------------------------------------------------------------------
    -- 7) review
    ---------------------------------------------------------------------------
    EXECUTE format($f$
        CREATE TABLE IF NOT EXISTS %I.review (
            review_id SERIAL PRIMARY KEY,
            iro_id INT NOT NULL,
            tenant_id INT NOT NULL,
            iro_version_id INT,
            reviewer_id INT NOT NULL,
            status VARCHAR(50) NOT NULL DEFAULT 'Draft',
            notes TEXT NOT NULL DEFAULT '',
            created_on TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_on TIMESTAMP NOT NULL DEFAULT NOW(),
            CONSTRAINT review_iro_fk
                FOREIGN KEY (iro_id)
                REFERENCES %I.iro(iro_id)
                ON DELETE CASCADE,
            CONSTRAINT review_tenant_fk
                FOREIGN KEY (tenant_id)
                REFERENCES public.tenant_config(tenant_id)
                ON DELETE CASCADE,
            CONSTRAINT review_version_fk
                FOREIGN KEY (iro_version_id)
                REFERENCES %I.iro_version(version_id)
                ON DELETE SET NULL
        );
        CREATE INDEX IF NOT EXISTS idx_review_tenant_id  ON %I.review (tenant_id);
        CREATE INDEX IF NOT EXISTS idx_review_iro_id     ON %I.review (iro_id);
        CREATE INDEX IF NOT EXISTS idx_review_version_id ON %I.review (iro_version_id);
        CREATE INDEX IF NOT EXISTS idx_review_status     ON %I.review (status);
    $f$, schema_name, schema_name, schema_name, schema_name);

    ---------------------------------------------------------------------------
    -- 8) signoff
    ---------------------------------------------------------------------------
    EXECUTE format($f$
        CREATE TABLE IF NOT EXISTS %I.signoff (
            signoff_id SERIAL PRIMARY KEY,
            review_id INT NOT NULL,
            tenant_id INT NOT NULL,
            iro_version_id INT,
            signed_by INT NOT NULL,
            signed_on TIMESTAMP NOT NULL DEFAULT NOW(),
            signature_ref VARCHAR(255),
            comments TEXT NOT NULL DEFAULT '',
            CONSTRAINT signoff_review_fk
                FOREIGN KEY (review_id)
                REFERENCES %I.review(review_id)
                ON DELETE CASCADE,
            CONSTRAINT signoff_tenant_fk
                FOREIGN KEY (tenant_id)
                REFERENCES public.tenant_config(tenant_id)
                ON DELETE CASCADE,
            CONSTRAINT signoff_version_fk
                FOREIGN KEY (iro_version_id)
                REFERENCES %I.iro_version(version_id)
                ON DELETE SET NULL
        );
        CREATE INDEX IF NOT EXISTS idx_signoff_tenant_id ON %I.signoff (tenant_id);
        CREATE INDEX IF NOT EXISTS idx_signoff_review_id ON %I.signoff (review_id);
        CREATE INDEX IF NOT EXISTS idx_signoff_signed_by ON %I.signoff (signed_by);
    $f$, schema_name, schema_name, schema_name, schema_name);

    ---------------------------------------------------------------------------
    -- 9) audit_trail
    ---------------------------------------------------------------------------
    EXECUTE format($f$
        CREATE TABLE IF NOT EXISTS %I.audit_trail (
            audit_id SERIAL PRIMARY KEY,
            tenant_id INT NOT NULL,
            entity_type VARCHAR(50) NOT NULL,
            entity_id INT NOT NULL,
            action VARCHAR(50) NOT NULL,
            user_id INT NOT NULL,
            timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
            data_diff JSONB NOT NULL DEFAULT '{}',
            CONSTRAINT fk_audit_trail_tenant
                FOREIGN KEY (tenant_id)
                REFERENCES public.tenant_config(tenant_id)
                ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_audit_trail_tenant_id      ON %I.audit_trail (tenant_id);
        CREATE INDEX IF NOT EXISTS idx_audit_trail_entity_type_id ON %I.audit_trail (entity_type, entity_id);
        CREATE INDEX IF NOT EXISTS idx_audit_trail_timestamp      ON %I.audit_trail (timestamp);
    $f$, schema_name, schema_name, schema_name);

    ---------------------------------------------------------------------------
    -- 10) AUXILIARY TABLES
    ---------------------------------------------------------------------------
    EXECUTE format($f$
        CREATE TABLE IF NOT EXISTS %I.impact_materiality_def (
            def_id SERIAL PRIMARY KEY,
            tenant_id INT NOT NULL,
            version_num INT NOT NULL,
            dimension VARCHAR(50) NOT NULL,
            score_value INT NOT NULL CHECK (score_value BETWEEN 1 AND 5),
            definition_text TEXT NOT NULL,
            valid_from TIMESTAMP NOT NULL,
            valid_to TIMESTAMP,
            created_on TIMESTAMP NOT NULL DEFAULT NOW(),
            created_by INT NOT NULL,
            CONSTRAINT fk_tenant_impact_def
                FOREIGN KEY (tenant_id)
                REFERENCES public.tenant_config(tenant_id)
                ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_imp_mat_def_tenant_id   ON %I.impact_materiality_def (tenant_id);
        CREATE INDEX IF NOT EXISTS idx_imp_mat_def_version_dim ON %I.impact_materiality_def (version_num, dimension);
    $f$, schema_name, schema_name);

    EXECUTE format($f$
        CREATE TABLE IF NOT EXISTS %I.fin_materiality_weights (
            weight_id SERIAL PRIMARY KEY,
            tenant_id INT NOT NULL,
            version_num INT NOT NULL,
            dimension VARCHAR(50) NOT NULL,
            weight NUMERIC(5,2) NOT NULL,
            valid_from TIMESTAMP NOT NULL,
            valid_to TIMESTAMP,
            created_on TIMESTAMP NOT NULL DEFAULT NOW(),
            created_by INT NOT NULL,
            CONSTRAINT fk_tenant_fin_weights
                FOREIGN KEY (tenant_id)
                REFERENCES public.tenant_config(tenant_id)
                ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_fin_weights_tenant_id   ON %I.fin_materiality_weights (tenant_id);
        CREATE INDEX IF NOT EXISTS idx_fin_weights_version_dim ON %I.fin_materiality_weights (version_num, dimension);
    $f$, schema_name, schema_name);

    -- ***** FIXED HERE: added a third "schema_name" argument *****
    EXECUTE format($f$
        CREATE TABLE IF NOT EXISTS %I.fin_materiality_magnitude_def (
            def_id SERIAL PRIMARY KEY,
            tenant_id INT NOT NULL,
            version_num INT NOT NULL,
            score_value INT NOT NULL CHECK (score_value BETWEEN 1 AND 5),
            definition_text TEXT NOT NULL,
            valid_from TIMESTAMP NOT NULL,
            valid_to TIMESTAMP,
            created_on TIMESTAMP NOT NULL DEFAULT NOW(),
            created_by INT NOT NULL,
            CONSTRAINT fk_tenant_fin_magnitude_def
                FOREIGN KEY (tenant_id)
                REFERENCES public.tenant_config(tenant_id)
                ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_fin_mag_def_tenant_id     ON %I.fin_materiality_magnitude_def (tenant_id);
        CREATE INDEX IF NOT EXISTS idx_fin_mag_def_version_score ON %I.fin_materiality_magnitude_def (version_num, score_value);
    $f$, schema_name, schema_name, schema_name);

END;
$$ LANGUAGE plpgsql;

INSERT INTO public.tenant_config (tenant_name) VALUES ('test1') ON CONFLICT DO NOTHING;
INSERT INTO public.tenant_config (tenant_name) VALUES ('test2') ON CONFLICT DO NOTHING;

SELECT create_tenant_schema('test1');
SELECT create_tenant_schema('test2');

</init-scripts/01-init-schemas.sql>


</schema design>
## 1. SCHEMA DESIGN
### 1.1 Database Structure
- **Primary Engine**: **Amazon RDS (PostgreSQL)** with `Multi-AZ` support for high availability.  
- **Multi-Tenant Isolation Approach**:  
  - **Option 1**: **Separate Schemas** per tenant, each containing the same structure (tables, views, etc.).  
  - **Option 2**: **Single Schema** with **Row-Level Security (RLS)** filters on every table (each row stores a `tenant_id`).  

**Recommended Strategy**  
- Default approach is **separate schemas** for standard tenants (simplifies indexing and permission scoping).  
- For very small tenants or those comfortable sharing the same schema, use **RLS** for finer control with fewer schema objects.  
- For **premium or highly regulated** tenants, optionally migrate to a **dedicated database** or cluster.

### 1.2 Isolation Method
1. **Separate Schemas (Default)**  
   - Each tenant gets a schema named `tenant_{tenant_id}` (e.g., `tenant_abc`).  
   - Access to each schema is restricted via schema-level privileges.  
   - Eases bulk exports or backups by schema.  
2. **Row-Level Security (Alternative)**  
   - All tenants share one schema and table set.  
   - PostgreSQL RLS policies restrict rows based on `tenant_id` = user’s assigned tenant ID.  
   - Simpler ongoing schema maintenance but requires thorough RLS policy management.

### 1.3 Naming Conventions
- **Schemas**: `tenant_<tenant_name_or_id>` or `tenant_{uuid}` to guarantee uniqueness.  
- **Tables**: Use a consistent prefix or domain-based approach, for example:  
  - `iro`, `dm_assessment`, `review`, `signoff`, `audit_trail` (core domain tables).  
- **Columns**: Lowercase with underscores (e.g., `tenant_id`, `created_on`).  
- **Indexes**: Named as `idx_{table_name}_{column_name}` (e.g., `idx_iro_tenant_id`).

### 1.4 Core Tables 
Below is **an expanded definition** of each core table—**IRO**, **DMAssessment**, **Review**, **Signoff**, and **AuditTrail**—with detailed **columns, constraints, indexes, and best practices**. These definitions align with the **multi-tenant PostgreSQL** architecture and incorporate **tenant isolation**, **security**, and **compliance** needs as described in the broader solution design.


---

## 1. SCHEMA DESIGN

### 1.1 Database Structure
- **Primary Engine**: **Amazon RDS (PostgreSQL)** with `Multi-AZ` for high availability and automated backups.  
- **Multi-Tenant Isolation**:  
  - **Default**: Each tenant in its own PostgreSQL schema (`tenant_<tenant_id>`).  

### 1.2 Isolation Method
1. **Separate Schemas (Default)**  
   - Create the same set of tables/indexes per tenant schema.  
   - Simplifies permission scoping and data export per tenant.  


### 1.3 Naming Conventions
- **Schemas**: `tenant_{tenant_id}` or `tenant_{tenant_name}`.  
- **Tables**: snake_case with domain-based naming: `iro`, `iro_version`, `iro_relationship`, `impact_assessment`, `risk_opp_assessment`, `financial_materiality_def`, etc.  
- **Columns**: lowercase with underscores (`created_on`, `updated_on`).  
- **Indexes**: `idx_{table}_{column}`.  

---


## 2. CORE TABLES

### 2.1 **IRO**


> Represents **Impacts, Risks, and Opportunities**. Extended with new fields (ESRS, sustainability topics, value chain info, economic activity, etc.) and references to versioning.

```sql
CREATE TABLE IF NOT EXISTS tenant_xyz.iro (
    iro_id                SERIAL          PRIMARY KEY,
    tenant_id             INT             NOT NULL,

    -- Tracks which IRO Version is considered "current/approved"
    current_version_id    INT,

    -- High-level status of the IRO (e.g., 'Draft', 'Review', 'Approval')
    current_stage         VARCHAR(50) NOT NULL DEFAULT 'Draft',

    -- Basic categorization
    type               VARCHAR(20)     NOT NULL, -- Positive Impact/ Negative Impact / Risk / Opportunity
    source_of_iro         VARCHAR(255),                 -- optional text
    esrs_standard         VARCHAR(100),                 -- from a defined list
    
    -- Assessment tracking
    last_assessment_date  TIMESTAMP,
    assessment_count      INT              DEFAULT 0,
    last_assessment_score NUMERIC(5,2),    -- impact_materiality_score or financial_materiality_score depending on type

    -- Metadata
    created_on            TIMESTAMP   NOT NULL DEFAULT NOW(),
    updated_on            TIMESTAMP   NOT NULL DEFAULT NOW(),

    CONSTRAINT iro_tenant_fk
      FOREIGN KEY (tenant_id)
      REFERENCES tenant_xyz.tenant_config(tenant_id)
      ON DELETE CASCADE
);

CREATE INDEX idx_iro_tenant_id     ON tenant_xyz.iro (tenant_id);
CREATE INDEX idx_iro_stage         ON tenant_xyz.iro (current_stage);
CREATE INDEX idx_iro_esrs_standard ON tenant_xyz.iro (esrs_standard);
```

**Key Points**  
- **`current_version_id`** references the `iro_version(version_id)` representing the “approved” statement.  
- **Array columns** allow multiple entries for value chain levels, etc.  


---

### 2.2 **IRO_Version**

> Stores the **full textual version** of IRO statements. Enables iteration, review, and historical tracking.

```sql
CREATE TABLE IF NOT EXISTS tenant_xyz.iro_version (
    version_id         SERIAL          PRIMARY KEY,
    iro_id             INT             NOT NULL,
    tenant_id          INT             NOT NULL,

    version_number     INT             NOT NULL,  -- increments for each new version of the same IRO

    title              VARCHAR(255)    NOT NULL,
    description        TEXT            NOT NULL,

    sust_topic_level1     VARCHAR(100),                 -- from a defined list
    sust_topic_level2     VARCHAR(100),                 -- from a defined list
    sust_topic_level3     VARCHAR(100),                 -- optional
    value_chain_lv1       VARCHAR[]     DEFAULT '{}',    -- multiple possible
    value_chain_lv2       VARCHAR[]     DEFAULT '{}',    -- multiple possible
    economic_activity     VARCHAR[]     DEFAULT '{}',    -- multiple possible

    status             VARCHAR(50)     NOT NULL DEFAULT 'Draft',
        -- e.g., 'Draft', 'In_Review', 'Approved', 'Superseded'

    created_by         INT             NOT NULL,
    created_on         TIMESTAMP       NOT NULL DEFAULT NOW(),

    -- For splitting/merging references
    parent_version_id  INT,
    split_type         VARCHAR(50),    -- e.g., NULL, 'Split_From', 'Merged_From'

    CONSTRAINT fk_iro 
        FOREIGN KEY (iro_id) 
        REFERENCES tenant_xyz.iro(iro_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_tenant 
        FOREIGN KEY (tenant_id)
        REFERENCES tenant_xyz.tenant_config(tenant_id)
        ON DELETE CASCADE
);

CREATE INDEX idx_iro_version_iro_id     ON tenant_xyz.iro_version (iro_id);
CREATE INDEX idx_iro_version_tenant_id  ON tenant_xyz.iro_version (tenant_id);
CREATE INDEX idx_iro_version_status     ON tenant_xyz.iro_version (status);
```

**Key Points**  
- Each IRO can have multiple versions, each with its own text (`title`, `description`).  
- **Splitting/Merging** tracked via `parent_version_id` and `split_type`.  
- The parent `iro` table’s `current_version_id` references whichever version is deemed “officially approved.”

---

### 2.3 **IRO_Relationship**

> Tracks how different IROs split or merge over time at the **IRO**-level (not just version-level).

```sql
CREATE TABLE IF NOT EXISTS tenant_xyz.iro_relationship (
    relationship_id     SERIAL          PRIMARY KEY,
    tenant_id           INT             NOT NULL,
    
    source_iro_id       INT             NOT NULL,
    target_iro_id       INT             NOT NULL,
    relationship_type   VARCHAR(50)     NOT NULL,
        -- e.g., 'Split_Into', 'Merged_From', etc.

    created_on          TIMESTAMP       NOT NULL DEFAULT NOW(),
    created_by          INT             NOT NULL,
    notes               TEXT,

    CONSTRAINT fk_tenant
        FOREIGN KEY (tenant_id)
        REFERENCES tenant_xyz.tenant_config(tenant_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_source_iro
        FOREIGN KEY (source_iro_id)
        REFERENCES tenant_xyz.iro(iro_id),
    CONSTRAINT fk_target_iro
        FOREIGN KEY (target_iro_id)
        REFERENCES tenant_xyz.iro(iro_id)
);

CREATE INDEX idx_iro_relationship_tenant_id  ON tenant_xyz.iro_relationship (tenant_id);
CREATE INDEX idx_iro_relationship_src_tgt    ON tenant_xyz.iro_relationship (source_iro_id, target_iro_id);
```

**Key Points**  
- Captures top-level changes such as “IRO #1 was split into IRO #2 and #3.”  
- Maintains auditability of IRO lineage aside from version iterations.

---

### 2.4 **Impact Assessment** (for negative/positive impact IROs)

> Formerly part of DMAssessment, now **split** into a distinct table for **Impact** scenarios.

```sql
CREATE TABLE IF NOT EXISTS tenant_xyz.impact_assessment (
    impact_assessment_id     SERIAL       PRIMARY KEY,
    iro_id                   INT          NOT NULL,
    tenant_id                INT          NOT NULL,

    -- Version references for definition changes
    impact_materiality_def_version_id INT,  -- references the version of definitions used

    time_horizon            VARCHAR(20)  NOT NULL,  -- e.g., 'Short', 'Medium', 'Long'
    actual_or_potential     -- actual or potential
    related_to_human_rights -- yes or no

    scale_score             INT CHECK (scale_score BETWEEN 1 AND 5),
    scale_rationale         TEXT,
    scope_score             INT CHECK (scope_score BETWEEN 1 AND 5),
    scope_rationale         TEXT,
    irremediability_score   INT CHECK (irremediability_score BETWEEN 1 AND 5),
    irremediability_rationale TEXT,

    likelihood_score        INT CHECK (likelihood_score BETWEEN 1 AND 5),
    likelihood_rationale    TEXT,

    severity_score          NUMERIC(5,2),
    impact_materiality_score NUMERIC(5,2),

    overall_rationale       TEXT,
    related_documents       TEXT,  -- or JSON, storing links to attachments

    created_on              TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_on              TIMESTAMP NOT NULL DEFAULT NOW(),


    CONSTRAINT fk_impact_iro
        FOREIGN KEY (iro_id)
        REFERENCES tenant_xyz.iro(iro_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_impact_tenant
        FOREIGN KEY (tenant_id)
        REFERENCES tenant_xyz.tenant_config(tenant_id)
        ON DELETE CASCADE
);

CREATE INDEX idx_impact_assessment_tenant_id ON tenant_xyz.impact_assessment (tenant_id);
CREATE INDEX idx_impact_assessment_iro_id    ON tenant_xyz.impact_assessment (iro_id);
```

**Key Points**  
- **`impact_materiality_def_version_id`** references the version of the **impact materiality definitions** that were current at the time of assessment (see [3.1] below).  
- **Negative Impacts** typically use `irremediability_score`. For positive impacts, it can be zero or NULL, and the “severity_score” calculation would exclude it.  
- **`impact_materiality_score`** is (roughly) the average of `severity_score` and `likelihood_score`. Computations can occur in the app or via triggers.

---

### 2.5 **Risk & Opportunities Assessment** (for “Risk” or “Opportunity” IROs)


> Formerly part of DMAssessment, now **split** into a distinct table for **Risk/Opportunity** scenarios.

```sql
CREATE TABLE IF NOT EXISTS tenant_xyz.risk_opp_assessment (
    risk_opp_assessment_id      SERIAL       PRIMARY KEY,
    iro_id                      INT          NOT NULL,
    tenant_id                   INT          NOT NULL,

    -- Version references for definition changes
    fin_materiality_def_version_id INT,  -- references the version of definitions/weights used

    time_horizon                VARCHAR(20)  NOT NULL,  -- 'Short', 'Medium', 'Long'

    workforce_risk              INT CHECK (workforce_risk BETWEEN 1 AND 5),
    workforce_risk_rationale    TEXT,
    operational_risk            INT CHECK (operational_risk BETWEEN 1 AND 5),
    operational_risk_rationale  TEXT,
    cost_of_capital_risk        INT CHECK (cost_of_capital_risk BETWEEN 1 AND 5),
    cost_of_capital_risk_rationale TEXT,
    reputational_risk           INT CHECK (reputational_risk BETWEEN 1 AND 5),
    reputational_risk_rationale TEXT,
    legal_compliance_risk       INT CHECK (legal_compliance_risk BETWEEN 1 AND 5),
    legal_compliance_risk_rationale TEXT,

    likelihood_score            INT CHECK (likelihood_score BETWEEN 1 AND 5),
    likelihood_rationale        TEXT,

    financial_magnitude_score   NUMERIC(5,2),
    financial_materiality_score NUMERIC(5,2),

    overall_rationale           TEXT,
    related_documents           TEXT,

    created_on                  TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_on                  TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_risk_opp_iro
        FOREIGN KEY (iro_id)
        REFERENCES tenant_xyz.iro(iro_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_risk_opp_tenant
        FOREIGN KEY (tenant_id)
        REFERENCES tenant_xyz.tenant_config(tenant_id)
        ON DELETE CASCADE
);

CREATE INDEX idx_risk_opp_assessment_tenant_id ON tenant_xyz.risk_opp_assessment (tenant_id);
CREATE INDEX idx_risk_opp_assessment_iro_id    ON tenant_xyz.risk_opp_assessment (iro_id);
```

**Key Points**  
- **`fin_materiality_def_version_id`** references the version of **financial materiality definitions/weights** that were current at the time of assessment (see [3.2] / [3.3] below).  
- **`magnitude_score`** is typically a weighted average of workforce, operational, cost of capital, reputational, and legal compliance risks based on the **weights** table.  
- **`financial_materiality_score`** is an average of `magnitude_score` and `likelihood_score`.

---

### 2.6 **Review**

> Tracks workflow reviews as an IRO (or IRO version) progresses through “Draft,” “Review,” “Approval,” etc.

```sql
CREATE TABLE IF NOT EXISTS tenant_xyz.review (
    review_id      SERIAL         PRIMARY KEY,
    iro_id         INT            NOT NULL,
    tenant_id      INT            NOT NULL,

    -- Optionally reference specific IRO version
    iro_version_id INT,

    reviewer_id    INT            NOT NULL, 
    status         VARCHAR(50)    NOT NULL DEFAULT 'Draft', 
        -- e.g., 'Draft', 'In_Review', 'Approved', 'Rejected', ...
    notes          TEXT           NOT NULL DEFAULT '',

    created_on     TIMESTAMP      NOT NULL DEFAULT NOW(),
    updated_on     TIMESTAMP      NOT NULL DEFAULT NOW(),

    CONSTRAINT review_iro_fk
        FOREIGN KEY (iro_id)
        REFERENCES tenant_xyz.iro(iro_id)
        ON DELETE CASCADE,
    CONSTRAINT review_tenant_fk
        FOREIGN KEY (tenant_id)
        REFERENCES tenant_xyz.tenant_config(tenant_id)
        ON DELETE CASCADE,
    CONSTRAINT review_version_fk
        FOREIGN KEY (iro_version_id)
        REFERENCES tenant_xyz.iro_version(version_id)
        ON DELETE SET NULL
);

CREATE INDEX idx_review_tenant_id      ON tenant_xyz.review (tenant_id);
CREATE INDEX idx_review_iro_id         ON tenant_xyz.review (iro_id);
CREATE INDEX idx_review_version_id     ON tenant_xyz.review (iro_version_id);
CREATE INDEX idx_review_status         ON tenant_xyz.review (status);
```

**Key Points**  
- **`iro_version_id`** is optional but clarifies which textual version is under review.  
- Possible stages include “Draft,” “Pending_Review,” “Approved,” “Rejected,” “Closed,” etc.

---

### 2.7 **Signoff**

> Records final approvals or eSignatures after a review cycle. Optionally references a specific version.

```sql
CREATE TABLE IF NOT EXISTS tenant_xyz.signoff (
    signoff_id    SERIAL        PRIMARY KEY,
    review_id     INT           NOT NULL,
    tenant_id     INT           NOT NULL,

    iro_version_id INT,  -- optional reference to the version being signed off

    signed_by     INT           NOT NULL,
    signed_on     TIMESTAMP     NOT NULL DEFAULT NOW(),
    signature_ref VARCHAR(255),
    comments      TEXT          NOT NULL DEFAULT '',

    CONSTRAINT signoff_review_fk
        FOREIGN KEY (review_id)
        REFERENCES tenant_xyz.review(review_id)
        ON DELETE CASCADE,
    CONSTRAINT signoff_tenant_fk
        FOREIGN KEY (tenant_id)
        REFERENCES tenant_xyz.tenant_config(tenant_id)
        ON DELETE CASCADE,
    CONSTRAINT signoff_version_fk
        FOREIGN KEY (iro_version_id)
        REFERENCES tenant_xyz.iro_version(version_id)
        ON DELETE SET NULL
);

CREATE INDEX idx_signoff_tenant_id   ON tenant_xyz.signoff (tenant_id);
CREATE INDEX idx_signoff_review_id   ON tenant_xyz.signoff (review_id);
CREATE INDEX idx_signoff_signed_by   ON tenant_xyz.signoff (signed_by);
```

**Key Points**  
- Signoffs typically complete the workflow for that version.

---

### 2.8 **AuditTrail**

> Unchanged in structure, but references to new tables (e.g., `impact_assessment`, `risk_opp_assessment`) should be recognized in `entity_type`.

```sql
CREATE TABLE IF NOT EXISTS tenant_xyz.audit_trail (
    audit_id     SERIAL       PRIMARY KEY,
    tenant_id    INT          NOT NULL,
    entity_type  VARCHAR(50)  NOT NULL,
        -- 'IRO', 'IRO_VERSION', 'IMPACT_ASSESSMENT', 'RISK_OPP_ASSESSMENT', etc.
    entity_id    INT          NOT NULL,
    action       VARCHAR(50)  NOT NULL,
    user_id      INT          NOT NULL,
    timestamp    TIMESTAMP    NOT NULL DEFAULT NOW(),
    data_diff    JSONB        NOT NULL DEFAULT '{}'
);

CREATE INDEX idx_audit_trail_tenant_id       ON tenant_xyz.audit_trail (tenant_id);
CREATE INDEX idx_audit_trail_entity_type_id  ON tenant_xyz.audit_trail (entity_type, entity_id);
CREATE INDEX idx_audit_trail_timestamp       ON tenant_xyz.audit_trail (timestamp);
```

**Key Points**  
- Ensure `entity_type` enumerates the new tables: “IMPACT_ASSESSMENT,” “RISK_OPP_ASSESSMENT,” etc.  
- Consider partitioning or archiving older logs for performance.

---

## 3. AUXILIARY TABLES (Definitions & Weights with Version Tracking)

The following tables store **dynamic definitions** for both **impact** and **financial** materiality. They allow changes over time (by incrementing **version**), and each assessment references the version used (as shown in [2.4] and [2.5]).

### 3.1 **Impact Materiality Definitions**


Stores how the 1-5 **scale**, **scope**, and **irremediability** ratings are defined for each version.  
Each row is a single “dimension + score” definition. Could also unify them, but splitting them line-by-line offers flexibility.

```sql
CREATE TABLE IF NOT EXISTS tenant_xyz.impact_materiality_def (
    def_id        SERIAL       PRIMARY KEY,
    tenant_id     INT          NOT NULL,

    version_num   INT          NOT NULL,
    dimension     VARCHAR(50)  NOT NULL,  
       -- ONLY 'scale', 'scope', 'irremediability', 'likelihood'
    score_value   INT          NOT NULL CHECK (score_value BETWEEN 1 AND 5),
    definition_text TEXT       NOT NULL,  
       -- textual explanation of what "3" means for 'scale' etc.

    valid_from    TIMESTAMP    NOT NULL, 
    valid_to      TIMESTAMP,  -- could be null if still valid

    created_on    TIMESTAMP    NOT NULL DEFAULT NOW(),
    created_by    INT          NOT NULL,

    CONSTRAINT fk_tenant_impact_def
      FOREIGN KEY (tenant_id)
      REFERENCES tenant_xyz.tenant_config(tenant_id)
      ON DELETE CASCADE
);

CREATE INDEX idx_imp_mat_def_tenant_id   ON tenant_xyz.impact_materiality_def (tenant_id);
CREATE INDEX idx_imp_mat_def_version_dim ON tenant_xyz.impact_materiality_def (version_num, dimension);
```

**Usage**  
- **`dimension`**: 'scale', 'scope', or 'irremediability'.  
- **`version_num`** increments when definitions change.  
- Assessments record `impact_materiality_def_version_id` to indicate which version was used.  

---

### 3.2 **Financial Materiality Weights**

Stores weights for each risk category (e.g., workforce, operational, etc.) that determine how `magnitude_score` is computed. Multiple rows per version if each dimension’s weight is separate.

```sql
CREATE TABLE IF NOT EXISTS tenant_xyz.fin_materiality_weights (
    weight_id    SERIAL       PRIMARY KEY,
    tenant_id    INT          NOT NULL,

    version_num  INT          NOT NULL,

    -- e.g. dimension could be 'workforce', 'operational', etc.
    dimension    VARCHAR(50)  NOT NULL,
    weight       NUMERIC(5,2) NOT NULL, 
       -- ratio in range [0,1] or a relative weighting

    valid_from   TIMESTAMP    NOT NULL,
    valid_to     TIMESTAMP,

    created_on   TIMESTAMP    NOT NULL DEFAULT NOW(),
    created_by   INT          NOT NULL,

    CONSTRAINT fk_tenant_fin_weights
      FOREIGN KEY (tenant_id)
      REFERENCES tenant_xyz.tenant_config(tenant_id)
      ON DELETE CASCADE
);

CREATE INDEX idx_fin_weights_tenant_id     ON tenant_xyz.fin_materiality_weights (tenant_id);
CREATE INDEX idx_fin_weights_version_dim   ON tenant_xyz.fin_materiality_weights (version_num, dimension);
```

**Usage**  
- Summation of all dimensions’ weights for a given version typically equals 1.0 (or 100%).  
- When an assessment references `fin_materiality_def_version_id`, it uses the corresponding set of records in this table to calculate the weighted average.  

---

### 3.3 **Financial Materiality Magnitude Scale Definitions**

Stores the textual 1-5 definitions for *magnitude* rating across each dimension. If the same textual definition applies to all categories, you might store them in a single dimension or simply store “magnitude” as a dimension. Otherwise, you can extend similarly to `impact_materiality_def`.

```sql
CREATE TABLE IF NOT EXISTS tenant_xyz.fin_materiality_magnitude_def (
    def_id       SERIAL       PRIMARY KEY,
    tenant_id    INT          NOT NULL,

    version_num  INT          NOT NULL,
    score_value  INT          NOT NULL CHECK (score_value BETWEEN 1 AND 5),
    definition_text TEXT      NOT NULL,  
       -- textual definition of what a '3' means for magnitude
    
    valid_from   TIMESTAMP    NOT NULL,
    valid_to     TIMESTAMP,

    created_on   TIMESTAMP    NOT NULL DEFAULT NOW(),
    created_by   INT          NOT NULL,

    CONSTRAINT fk_tenant_fin_magnitude_def
      FOREIGN KEY (tenant_id)
      REFERENCES tenant_xyz.tenant_config(tenant_id)
      ON DELETE CASCADE
);

CREATE INDEX idx_fin_mag_def_tenant_id     ON tenant_xyz.fin_materiality_magnitude_def (tenant_id);
CREATE INDEX idx_fin_mag_def_version_score ON tenant_xyz.fin_materiality_magnitude_def (version_num, score_value);
```

**Usage**  
- If a dimension-specific definition is needed, add a `dimension` column or replicate `fin_materiality_weights` approach.  
- The `fin_materiality_def_version_id` in `risk_opp_assessment` identifies which version of magnitude definitions was valid at the time.

</schema design>

<componse.yaml>
services:
  web:
    build: .
    command: sh -c "python manage.py migrate && gunicorn core.wsgi:application --bind 0.0.0.0:8000"
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    environment:
      - DJANGO_SETTINGS_MODULE=core.settings.local
      - DATABASE_URL=postgres://dma_user:password@db:5432/dma_db
    depends_on:
      - db
      - redis

  db:
    image: postgres:14
    restart: always
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d  # Make sure this line exists
    environment:
      POSTGRES_USER: dma_user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: dma_db
    ports:
      - "5432:5432"  # Add this to make debugging easier



  redis:
    image: redis:7
    restart: always

  worker:
    build: .
    command: celery -A core worker --loglevel=info
    volumes:
      - .:/app
    environment:
      - DJANGO_SETTINGS_MODULE=core.settings.local
      - DATABASE_URL=postgres://dma_user:password@db:5432/dma_db
      - CELERY_BROKER_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis

volumes:
  postgres_data:
</compose.yaml>
</file>

</Concatenated Source Code>