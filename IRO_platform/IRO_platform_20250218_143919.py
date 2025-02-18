'''
Included Files:
- compose.yaml
- compose.yaml
- init-scripts/01-init-schemas.sql

'''

# Concatenated Source Code

<file path='compose.yaml'>
version: '3.11'  # Specify the Docker Compose version

services:
  # The Django web service, our main application container.
  web:
    build: .
    command: gunicorn core.wsgi:application --bind 0.0.0.0:8000
    volumes:
      - .:/app  # Mount your project directory to allow live code reloading.
    ports:
      - "8000:8000"  # Expose port 8000 locally.
    environment:
      - DJANGO_SETTINGS_MODULE=core.settings.local
      - DATABASE_URL=postgres://dma_user:password@db:5432/dma_db
    depends_on:
      - db
      - redis

  # The PostgreSQL database container.
  db:
    image: postgres:14
    restart: always
    volumes:
      - postgres_data:/var/lib/postgresql/data  # Persist database data.
      - ./init-scripts:/docker-entrypoint-initdb.d  # Add this line
    environment:
      POSTGRES_USER: dma_user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: dma_db

  # Redis container to serve as the message broker for background tasks.
  redis:
    image: redis:7
    restart: always

  # The Celery worker container for handling asynchronous tasks.
  worker:
    build: .
    command: celery -A core worker --loglevel=info
    volumes:
      - .:/app  # Mount your project directory for consistent code access.
    environment:
      - DJANGO_SETTINGS_MODULE=core.settings.local
      - DATABASE_URL=postgres://dma_user:password@db:5432/dma_db
      - CELERY_BROKER_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis

volumes:
  postgres_data:

</file>

<file path='compose.yaml'>
version: '3.11'  # Specify the Docker Compose version

services:
  # The Django web service, our main application container.
  web:
    build: .
    command: gunicorn core.wsgi:application --bind 0.0.0.0:8000
    volumes:
      - .:/app  # Mount your project directory to allow live code reloading.
    ports:
      - "8000:8000"  # Expose port 8000 locally.
    environment:
      - DJANGO_SETTINGS_MODULE=core.settings.local
      - DATABASE_URL=postgres://dma_user:password@db:5432/dma_db
    depends_on:
      - db
      - redis

  # The PostgreSQL database container.
  db:
    image: postgres:14
    restart: always
    volumes:
      - postgres_data:/var/lib/postgresql/data  # Persist database data.
      - ./init-scripts:/docker-entrypoint-initdb.d  # Add this line
    environment:
      POSTGRES_USER: dma_user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: dma_db

  # Redis container to serve as the message broker for background tasks.
  redis:
    image: redis:7
    restart: always

  # The Celery worker container for handling asynchronous tasks.
  worker:
    build: .
    command: celery -A core worker --loglevel=info
    volumes:
      - .:/app  # Mount your project directory for consistent code access.
    environment:
      - DJANGO_SETTINGS_MODULE=core.settings.local
      - DATABASE_URL=postgres://dma_user:password@db:5432/dma_db
      - CELERY_BROKER_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis

volumes:
  postgres_data:

</file>

<file path='init-scripts/01-init-schemas.sql'>
-- Create a function to initialize tenant schemas
CREATE OR REPLACE FUNCTION create_tenant_schema(tenant_name TEXT) RETURNS void AS $$
BEGIN
    -- Create schema
    EXECUTE format('CREATE SCHEMA IF NOT EXISTS tenant_%I', tenant_name);
    
    -- Create core tables in the tenant schema
    EXECUTE format('
        CREATE TABLE tenant_%I.iro (
            iro_id SERIAL PRIMARY KEY,
            tenant_id INT NOT NULL,
            current_version_id INT,
            current_stage VARCHAR(50) NOT NULL DEFAULT ''Draft'',
            type VARCHAR(20) NOT NULL,
            source_of_iro VARCHAR(255),
            esrs_standard VARCHAR(100),
            last_assessment_date TIMESTAMP,
            assessment_count INT DEFAULT 0,
            last_assessment_score NUMERIC(5,2),
            created_on TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_on TIMESTAMP NOT NULL DEFAULT NOW()
        )', tenant_name);

    -- Add similar CREATE TABLE statements for other tables
    -- (iro_version, iro_relationship, impact_assessment, etc.)
END;
$$ LANGUAGE plpgsql;

-- Create test tenants for development
SELECT create_tenant_schema('test1');
SELECT create_tenant_schema('test2');
</file>

"""
<goal>


</goal>


<output instruction>
1) Explain 
2) Give me the COMPLETE UPDATED VERSION of each script that needs to be updated
</output instruction>
"""
