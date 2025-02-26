<issue to solve>
the UI is not showing any of the sample data that should be prepopulated in the database. The UI should show 2 tenants, each with 5 IROs that are fully assessed. 

</issue to solve>

<startup log>
(.venv) juanfuentes@Juans-MacBook-Pro IRO_platform % ./run_local.sh
Building Docker images...
[+] Running 5/5
 ✔ Container iro_platform-web-1     Removed                                                             10.6s 
 ✔ Container iro_platform-worker-1  Removed                                                              4.2s 
 ✔ Container iro_platform-db-1      Removed                                                              0.6s 
 ✔ Container iro_platform-redis-1   Removed                                                              0.5s 
 ✔ Network iro_platform_default     Removed                                                              0.3s 
[+] Building 42.2s (20/24)                                                               docker:desktop-linux
 => [worker internal] load build definition from Dockerfile                                              0.0s
 => => transferring dockerfile: 927B                                                                     0.0s
 => [web internal] load build definition from Dockerfile                                                 0.0s
 => => transferring dockerfile: 927B                                                                     0.0s
 => [worker internal] load metadata for docker.io/library/python:3.11-slim                               1.0s
 => [web auth] library/python:pull token for registry-1.docker.io                                        0.0s
 => [worker internal] load .dockerignore                                                                 0.0s
 => => transferring context: 2B                                                                          0.0s
 => [web internal] load .dockerignore                                                                    0.0s
 => => transferring context: 2B                                                                          0.0s
 => [worker 1/8] FROM docker.io/library/python:3.11-slim@sha256:614c8691ab74150465ec9123378cd4dde7a6e57  0.0s
 => => resolve docker.io/library/python:3.11-slim@sha256:614c8691ab74150465ec9123378cd4dde7a6e57be9e558  0.0s
 => [worker internal] load build context                                                                 1.3s
 => => transferring context: 1.24MB                                                                      1.2s
 => [web internal] load build context                                                                    1.3s
 => => transferring context: 1.24MB                                                                      1.2s
 => CACHED [web 2/8] RUN apt-get update     && apt-get install -y postgresql-client     && rm -rf /var/  0.0s
 => CACHED [web 3/8] RUN groupadd -r appuser && useradd -r -g appuser appuser                            0.0s
 => CACHED [web 4/8] WORKDIR /app                                                                        0.0s
 => CACHED [web 5/8] COPY requirements.txt /app/                                                         0.0s
 => CACHED [worker 6/8] RUN pip install --no-cache-dir -r requirements.txt                               0.0s
 => [worker 7/8] COPY . /app/                                                                            6.0s
 => [web 8/8] RUN chown -R appuser:appuser /app                                                         16.4s
 => [worker] exporting to image                                                                         14.5s
 => => exporting layers                                                                                  6.2s
 => => exporting manifest sha256:85813321359583254297bac61b689442ce2cd96c7890c63ebb0c519444fb36d6        0.0s
 => => exporting config sha256:a05e6e86ab263a8d190cea4a30cfcb0c6e671bd36d3604b3627bee242cc5ffed          0.0s
 => => exporting attestation manifest sha256:ecf6a8fcf6e0f7f8b07d07a690fcf35d4774fdd22af1990ae858deb936  0.0s
 => => exporting manifest list sha256:70ee1992b6a367c0264c390a25d8f74cd92f2085a06528be06a480bf5b16ded3   0.0s
 => => naming to docker.io/library/iro_platform-worker:latest                                            0.0s
 => => unpacking to docker.io/library/iro_platform-worker:latest                                         8.0s
 => [web] exporting to image                                                                            14.5s
 => => exporting layers                                                                                  6.2s
 => => exporting manifest sha256:1cde3b8e3c70d3b96c337bdaa2c708700f8c7cfd7be4cfecd6a74153b8291726        0.0s
 => => exporting config sha256:7a5960be1c16734585f089a4cff7a3a3e353d9af558ca07edec055e4e39b055e          0.0s
 => => exporting attestation manifest sha256:9e1b48c5ed46f97c1fbd661dfa7a1f638d899d8645a3f79c34a2ad1042  0.0s
 => => exporting manifest list sha256:de49227843fcb368c9a42f235968119280b595a6eeb4554683537ca07b479224   0.0s
 => => naming to docker.io/library/iro_platform-web:latest                                               0.0s
 => => unpacking to docker.io/library/iro_platform-web:latest                                            8.1s
 => [worker] resolving provenance for metadata file                                                      0.1s
 => [web] resolving provenance for metadata file                                                         0.1s
[+] Building 2/2
 ✔ web     Built                                                                                         0.0s 
 ✔ worker  Built                                                                                         0.0s 
Starting containers in the background...
[+] Running 5/5
 ✔ Network iro_platform_default     Created                                                              0.1s 
 ✔ Container iro_platform-db-1      Healthy                                                             10.5s 
 ✔ Container iro_platform-redis-1   Healthy                                                             10.5s 
 ✔ Container iro_platform-web-1     Started                                                              8.0s 
 ✔ Container iro_platform-worker-1  Started                                                              8.0s 
Waiting for the web container to finish startup...
Checking if migrations are needed...
No changes detected
No migrations needed.
Running shared migrations...
=== Starting migration
Operations to perform:
  Apply all migrations: admin, assessments, auth, contenttypes, guardian, sessions, tenants
Running migrations:
  No migrations to apply.
Creating or updating default tenant...
Tenant named "default" already exists. Checking associated domain...
Domain "localhost" also already exists. No changes were made.
Running tenant migrations...
=== Starting migration
Operations to perform:
  Apply all migrations: admin, assessments, auth, contenttypes, guardian, sessions, tenants
Running migrations:
  No migrations to apply.
=== Starting migration
Operations to perform:
  Apply all migrations: admin, assessments, auth, contenttypes, guardian, sessions, tenants
Running migrations:
  No migrations to apply.
=== Starting migration
Operations to perform:
  Apply all migrations: admin, assessments, auth, contenttypes, guardian, sessions, tenants
Running migrations:
  No migrations to apply.
Prepopulating sample data (2 tenants, each with 5 IROs fully assessed)...
Tenant "tenant1" already exists. Using the existing tenant.
Current schema before IRO creation: public
Found 5 existing IROs for tenant tenant1
Tenant "tenant1" already has 5 IRO(s). Skipping creation.
Tenant "tenant2" already exists. Using the existing tenant.
Current schema before IRO creation: public
Found 5 existing IROs for tenant tenant2
Tenant "tenant2" already has 5 IRO(s). Skipping creation.
Tailing logs. Press Ctrl+C to stop.
redis-1   | 1:C 26 Feb 2025 18:12:17.973 * oO0OoO0OoO0Oo Redis is starting oO0OoO0OoO0Oo
redis-1   | 1:C 26 Feb 2025 18:12:17.973 * Redis version=7.4.2, bits=64, commit=00000000, modified=0, pid=1, just started
redis-1   | 1:C 26 Feb 2025 18:12:17.973 # Warning: no config file specified, using the default config. In order to specify a config file use redis-server /path/to/redis.conf
redis-1   | 1:M 26 Feb 2025 18:12:17.975 * monotonic clock: POSIX clock_gettime
redis-1   | 1:M 26 Feb 2025 18:12:17.985 * Running mode=standalone, port=6379.
redis-1   | 1:M 26 Feb 2025 18:12:17.986 * Server initialized
db-1      | 
worker-1  |  
worker-1  |  -------------- celery@c8ca9959d29a v5.2.7 (dawn-chorus)
worker-1  | --- ***** ----- 
web-1     | db:5432 - accepting connections
web-1     | No changes detected in app 'tenants'
web-1     | No changes detected
redis-1   | 1:M 26 Feb 2025 18:12:17.986 * Ready to accept connections tcp
db-1      | PostgreSQL Database directory appears to contain a database; Skipping initialization
db-1      | 
web-1     | === Starting migration
web-1     | Operations to perform:
db-1      | 2025-02-26 18:12:18.168 UTC [1] LOG:  starting PostgreSQL 14.16 (Debian 14.16-1.pgdg120+1) on aarch64-unknown-linux-gnu, compiled by gcc (Debian 12.2.0-14) 12.2.0, 64-bit
db-1      | 2025-02-26 18:12:18.173 UTC [1] LOG:  listening on IPv4 address "0.0.0.0", port 5432
db-1      | 2025-02-26 18:12:18.173 UTC [1] LOG:  listening on IPv6 address "::", port 5432
web-1     |   Apply all migrations: admin, assessments, auth, contenttypes, guardian, sessions, tenants
web-1     | Running migrations:
db-1      | 2025-02-26 18:12:18.185 UTC [1] LOG:  listening on Unix socket "/var/run/postgresql/.s.PGSQL.5432"
db-1      | 2025-02-26 18:12:18.208 UTC [27] LOG:  database system was shut down at 2025-02-26 18:11:28 UTC
db-1      | 2025-02-26 18:12:18.276 UTC [1] LOG:  database system is ready to accept connections
web-1     |   No migrations to apply.
web-1     | Tenant named "default" already exists. Checking associated domain...
web-1     | Domain "localhost" also already exists. No changes were made.
worker-1  | -- ******* ---- Linux-6.12.5-linuxkit-aarch64-with-glibc2.36 2025-02-26 18:12:25
worker-1  | - *** --- * --- 
worker-1  | - ** ---------- [config]
worker-1  | - ** ---------- .> app:         core:0xffff8fc75290
worker-1  | - ** ---------- .> transport:   redis://redis:6379/0
worker-1  | - ** ---------- .> results:     disabled://
worker-1  | - *** --- * --- .> concurrency: 8 (prefork)
worker-1  | -- ******* ---- .> task events: OFF (enable -E to monitor tasks in this worker)
worker-1  | --- ***** ----- 
worker-1  |  -------------- [queues]
worker-1  |                 .> celery           exchange=celery(direct) key=celery
worker-1  |                 
worker-1  | 
worker-1  | [tasks]
web-1     | === Starting migration
web-1     | Operations to perform:
web-1     |   Apply all migrations: admin, assessments, auth, contenttypes, guardian, sessions, tenants
web-1     | Running migrations:
web-1     |   No migrations to apply.
web-1     | === Starting migration
web-1     | Operations to perform:
worker-1  |   . apps.assessments.tasks.example_task
worker-1  | 
worker-1  | [2025-02-26 18:12:26,429: INFO/MainProcess] Connected to redis://redis:6379/0
web-1     |   Apply all migrations: admin, assessments, auth, contenttypes, guardian, sessions, tenants
web-1     | Running migrations:
web-1     |   No migrations to apply.
web-1     | === Starting migration
web-1     | Operations to perform:
worker-1  | [2025-02-26 18:12:26,438: INFO/MainProcess] mingle: searching for neighbors
worker-1  | [2025-02-26 18:12:27,450: INFO/MainProcess] mingle: all alone
worker-1  | [2025-02-26 18:12:27,478: WARNING/MainProcess] /usr/local/lib/python3.11/site-packages/celery/fixups/django.py:203: UserWarning: Using settings.DEBUG leads to a memory
worker-1  |             leak, never use this setting in production environments!
web-1     |   Apply all migrations: admin, assessments, auth, contenttypes, guardian, sessions, tenants
web-1     | Running migrations:
web-1     |   No migrations to apply.
web-1     | Tenant "tenant1" already exists. Using the existing tenant.
web-1     | Current schema before IRO creation: public
worker-1  |   warnings.warn('''Using settings.DEBUG leads to a memory
worker-1  | 
worker-1  | [2025-02-26 18:12:27,478: INFO/MainProcess] celery@c8ca9959d29a ready.
web-1     | Found 5 existing IROs for tenant tenant1
web-1     | Tenant "tenant1" already has 5 IRO(s). Skipping creation.
web-1     | Tenant "tenant2" already exists. Using the existing tenant.
web-1     | Current schema before IRO creation: public
web-1     | Found 5 existing IROs for tenant tenant2
web-1     | Tenant "tenant2" already has 5 IRO(s). Skipping creation.
web-1     | Listing tables in tenant_tenant1 schema...
web-1     |                          List of relations
web-1     |      Schema     |             Name              | Type  |  Owner   
web-1     | ----------------+-------------------------------+-------+----------
web-1     |  tenant_tenant1 | assessment                    | table | dma_user
web-1     |  tenant_tenant1 | audit_trail                   | table | dma_user
web-1     |  tenant_tenant1 | django_migrations             | table | dma_user
web-1     |  tenant_tenant1 | fin_materiality_magnitude_def | table | dma_user
web-1     |  tenant_tenant1 | fin_materiality_weights       | table | dma_user
web-1     |  tenant_tenant1 | impact_assessment             | table | dma_user
web-1     |  tenant_tenant1 | impact_materiality_def        | table | dma_user
web-1     |  tenant_tenant1 | iro                           | table | dma_user
web-1     |  tenant_tenant1 | iro_relationship              | table | dma_user
web-1     |  tenant_tenant1 | iro_version                   | table | dma_user
web-1     |  tenant_tenant1 | review                        | table | dma_user
web-1     |  tenant_tenant1 | risk_opp_assessment           | table | dma_user
web-1     |  tenant_tenant1 | signoff                       | table | dma_user
web-1     | (13 rows)
web-1     | 
web-1     | Listing tables in tenant_tenant2 schema...
web-1     |                          List of relations
web-1     |      Schema     |             Name              | Type  |  Owner   
web-1     | ----------------+-------------------------------+-------+----------
web-1     |  tenant_tenant2 | assessment                    | table | dma_user
web-1     |  tenant_tenant2 | audit_trail                   | table | dma_user
web-1     |  tenant_tenant2 | django_migrations             | table | dma_user
web-1     |  tenant_tenant2 | fin_materiality_magnitude_def | table | dma_user
web-1     |  tenant_tenant2 | fin_materiality_weights       | table | dma_user
web-1     |  tenant_tenant2 | impact_assessment             | table | dma_user
web-1     |  tenant_tenant2 | impact_materiality_def        | table | dma_user
web-1     |  tenant_tenant2 | iro                           | table | dma_user
web-1     |  tenant_tenant2 | iro_relationship              | table | dma_user
web-1     |  tenant_tenant2 | iro_version                   | table | dma_user
web-1     |  tenant_tenant2 | review                        | table | dma_user
web-1     |  tenant_tenant2 | risk_opp_assessment           | table | dma_user
web-1     |  tenant_tenant2 | signoff                       | table | dma_user
web-1     | (13 rows)
web-1     | 
web-1     | 
web-1     | 162 static files copied to '/app/core/static'.
web-1     | [2025-02-26 18:12:34 +0000] [23] [INFO] Starting gunicorn 20.1.0
web-1     | [2025-02-26 18:12:34 +0000] [23] [INFO] Listening at: http://0.0.0.0:8000 (23)
web-1     | [2025-02-26 18:12:34 +0000] [23] [INFO] Using worker: sync
web-1     | [2025-02-26 18:12:34 +0000] [24] [INFO] Booting worker with pid: 24
</startup log>

<output instruction>
1) Reflect on 5-7 different possible sources of the problem, distill those down to most likely root cause 
2) Give me the COMPLETE UPDATED VERSION of each script that needs to be updated
</output instruction>



 <Tree of Included Files>
- Dockerfile
- Dockerfile
- apps/assessments/__init__.py
- apps/assessments/admin.py
- apps/assessments/api/serializers.py
- apps/assessments/api/urls.py
- apps/assessments/api/views.py
- apps/assessments/apps.py
- apps/assessments/migrations/0001_initial.py
- apps/assessments/migrations/0002_assessment_tenant.py
- apps/assessments/migrations/0003_alter_assessment_tenant.py
- apps/assessments/migrations/__init__.py
- apps/assessments/models.py
- apps/assessments/tasks.py
- apps/assessments/templatetags/__init__.py
- apps/assessments/templatetags/assessment_filters.py
- apps/assessments/urls.py
- apps/assessments/views.py
- core/__init__.py
- core/celery.py
- core/middleware/__init__.py
- core/middleware/context_middleware.py
- core/settings/__init__.py
- core/settings/base.py
- core/settings/local.py
- core/settings/production.py
- core/urls.py
- core/views.py
- core/wsgi.py
- docker-compose.yaml
- manage.py
- requirements.txt
- run_local.sh
- scripts/01-init-schemas.sql
- static/js/context_manager.js
- static/js/dashboard.js
- templates/assessments/assessment_form.html
- templates/assessments/assessment_list.html
- templates/assessments/iro_form.html
- templates/assessments/iro_list.html
- templates/base.html
- templates/components/context_selector.html
- templates/home.html
- tenants/admin.py
- tenants/api/serializers.py
- tenants/api/urls.py
- tenants/api/views.py
- tenants/apps.py
- tenants/management/commands/__init__.py
- tenants/management/commands/init_sample_data.py
- tenants/management/commands/init_tenant.py
- tenants/migrations/0001_initial.py
- tenants/migrations/__init__.py
- tenants/models.py
- tenants/urls.py
- tenants/views.py




 <Tree of Included Files>


<Concatenated Source Code>

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

# Create a non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . /app/

# Make sure the non-root user owns the application files
RUN chown -R appuser:appuser /app

# Switch to the non-root user
USER appuser

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

# Create a non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . /app/

# Make sure the non-root user owns the application files
RUN chown -R appuser:appuser /app

# Switch to the non-root user
USER appuser

# Default command (Docker Compose will typically override this)
CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000"]
</file>

<file path='apps/assessments/__init__.py'>

</file>

<file path='apps/assessments/admin.py'>
# apps/assessments/admin.py

from django.contrib import admin
from .models import (
    Assessment, IRO, IROVersion, IRORelationship, ImpactAssessment, 
    RiskOppAssessment, Review, Signoff, AuditTrail, 
    ImpactMaterialityDef, FinMaterialityWeights, FinMaterialityMagnitudeDef
)

@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description', 'created_on', 'updated_on')
    search_fields = ('name', 'description')
    list_filter = ('created_on',)

@admin.register(IRO)
class IROAdmin(admin.ModelAdmin):
    list_display = ('iro_id', 'tenant', 'type', 'current_stage',
                    'last_assessment_date', 'assessment_count')
    search_fields = ('type', 'source_of_iro', 'esrs_standard')
    list_filter = ('current_stage', 'esrs_standard', 'updated_on')

@admin.register(IROVersion)
class IROVersionAdmin(admin.ModelAdmin):
    list_display = ('version_id', 'iro', 'tenant', 'version_number', 'title', 
                    'status', 'created_on')
    search_fields = ('title', 'description', 'sust_topic_level1', 'sust_topic_level2')
    list_filter = ('status', 'created_on')

@admin.register(IRORelationship)
class IRORelationshipAdmin(admin.ModelAdmin):
    list_display = ('relationship_id', 'tenant', 'source_iro', 'target_iro', 'relationship_type')
    search_fields = ('relationship_type', 'notes')
    list_filter = ('relationship_type', 'created_on')

@admin.register(ImpactAssessment)
class ImpactAssessmentAdmin(admin.ModelAdmin):
    list_display = ('impact_assessment_id', 'iro', 'tenant', 'time_horizon',
                    'actual_or_potential', 'impact_materiality_score')
    list_filter = ('time_horizon', 'actual_or_potential')
    search_fields = ('overall_rationale',)

@admin.register(RiskOppAssessment)
class RiskOppAssessmentAdmin(admin.ModelAdmin):
    list_display = ('risk_opp_assessment_id', 'iro', 'tenant', 'time_horizon', 
                    'financial_materiality_score')
    list_filter = ('time_horizon',)
    search_fields = ('overall_rationale',)

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('review_id', 'iro', 'tenant', 'reviewer_id', 'status', 'updated_on')
    list_filter = ('status', 'created_on', 'updated_on')
    search_fields = ('notes',)

@admin.register(Signoff)
class SignoffAdmin(admin.ModelAdmin):
    list_display = ('signoff_id', 'review', 'tenant', 'signed_by', 'signed_on')
    list_filter = ('signed_on',)
    search_fields = ('comments', 'signature_ref')

@admin.register(AuditTrail)
class AuditTrailAdmin(admin.ModelAdmin):
    list_display = ('audit_id', 'tenant', 'entity_type', 'entity_id', 'action', 'timestamp')
    list_filter = ('entity_type', 'action', 'timestamp')
    search_fields = ('data_diff',)

@admin.register(ImpactMaterialityDef)
class ImpactMaterialityDefAdmin(admin.ModelAdmin):
    list_display = ('def_id', 'tenant', 'version_num', 'dimension', 'score_value', 'valid_from', 'valid_to')
    list_filter = ('dimension', 'score_value', 'valid_from', 'valid_to')
    search_fields = ('definition_text',)

@admin.register(FinMaterialityWeights)
class FinMaterialityWeightsAdmin(admin.ModelAdmin):
    list_display = ('weight_id', 'tenant', 'version_num', 'dimension', 'weight', 'valid_from', 'valid_to')
    list_filter = ('dimension', 'version_num', 'valid_from', 'valid_to')
    search_fields = ('dimension',)

@admin.register(FinMaterialityMagnitudeDef)
class FinMaterialityMagnitudeDefAdmin(admin.ModelAdmin):
    list_display = ('def_id', 'tenant', 'version_num', 'score_value', 'valid_from', 'valid_to')
    list_filter = ('version_num', 'score_value', 'valid_from', 'valid_to')
    search_fields = ('definition_text',)
</file>

<file path='apps/assessments/api/serializers.py'>
# apps/assessments/api/serializers.py
from rest_framework import serializers
from ..models import IRO

class IROSerializer(serializers.ModelSerializer):
    class Meta:
        model = IRO
        fields = "__all__"
</file>

<file path='apps/assessments/api/urls.py'>
# apps/assessments/api/urls.py
from rest_framework.routers import DefaultRouter
from .views import IROViewSet

router = DefaultRouter()
router.register(r'iros', IROViewSet, basename='iro')

urlpatterns = router.urls
</file>

<file path='apps/assessments/api/views.py'>
# apps/assessments/api/views.py
from rest_framework import viewsets, permissions
from ..models import IRO
from .serializers import IROSerializer
from ..views import ContextMixin  # Import the ContextMixin

class IROViewSet(ContextMixin, viewsets.ModelViewSet):
    """
    A ViewSet for viewing and editing IRO instances.
    """
    queryset = IRO.objects.all()
    serializer_class = IROSerializer
    permission_classes = [permissions.IsAuthenticated]  # ensure only authenticated users
</file>

<file path='apps/assessments/apps.py'>
# apps/assessments/apps.py
from django.apps import AppConfig

class AssessmentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.assessments'
    verbose_name = "Assessments"
</file>

<file path='apps/assessments/migrations/0001_initial.py'>
# Generated by Django 4.2 on 2025-02-25 01:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("tenants", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Assessment",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        help_text="Name of the assessment", max_length=200
                    ),
                ),
                (
                    "description",
                    models.TextField(blank=True, help_text="Optional description"),
                ),
                ("created_on", models.DateTimeField(auto_now_add=True)),
                ("updated_on", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "assessment",
            },
        ),
        migrations.CreateModel(
            name="IRO",
            fields=[
                ("iro_id", models.AutoField(primary_key=True, serialize=False)),
                ("current_version_id", models.IntegerField(blank=True, null=True)),
                ("current_stage", models.CharField(default="Draft", max_length=50)),
                ("type", models.CharField(max_length=20)),
                (
                    "source_of_iro",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                (
                    "esrs_standard",
                    models.CharField(blank=True, max_length=100, null=True),
                ),
                ("last_assessment_date", models.DateTimeField(blank=True, null=True)),
                ("assessment_count", models.IntegerField(default=0)),
                (
                    "last_assessment_score",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=5, null=True
                    ),
                ),
                ("created_on", models.DateTimeField(auto_now_add=True)),
                ("updated_on", models.DateTimeField(auto_now=True)),
                (
                    "tenant",
                    models.ForeignKey(
                        db_column="tenant_id",
                        on_delete=django.db.models.deletion.CASCADE,
                        to="tenants.tenantconfig",
                    ),
                ),
            ],
            options={
                "db_table": "iro",
            },
        ),
        migrations.CreateModel(
            name="IROVersion",
            fields=[
                ("version_id", models.AutoField(primary_key=True, serialize=False)),
                ("version_number", models.IntegerField()),
                ("title", models.CharField(max_length=255)),
                ("description", models.TextField()),
                (
                    "sust_topic_level1",
                    models.CharField(blank=True, max_length=100, null=True),
                ),
                (
                    "sust_topic_level2",
                    models.CharField(blank=True, max_length=100, null=True),
                ),
                (
                    "sust_topic_level3",
                    models.CharField(blank=True, max_length=100, null=True),
                ),
                ("value_chain_lv1", models.JSONField(default=list)),
                ("value_chain_lv2", models.JSONField(default=list)),
                ("economic_activity", models.JSONField(default=list)),
                ("status", models.CharField(default="Draft", max_length=50)),
                ("created_by", models.IntegerField()),
                ("created_on", models.DateTimeField(auto_now_add=True)),
                ("parent_version_id", models.IntegerField(blank=True, null=True)),
                ("split_type", models.CharField(blank=True, max_length=50, null=True)),
                (
                    "iro",
                    models.ForeignKey(
                        db_column="iro_id",
                        on_delete=django.db.models.deletion.CASCADE,
                        to="assessments.iro",
                    ),
                ),
                (
                    "tenant",
                    models.ForeignKey(
                        db_column="tenant_id",
                        on_delete=django.db.models.deletion.CASCADE,
                        to="tenants.tenantconfig",
                    ),
                ),
            ],
            options={
                "db_table": "iro_version",
            },
        ),
        migrations.CreateModel(
            name="Review",
            fields=[
                ("review_id", models.AutoField(primary_key=True, serialize=False)),
                ("reviewer_id", models.IntegerField()),
                ("status", models.CharField(default="Draft", max_length=50)),
                ("notes", models.TextField(blank=True, default="")),
                ("created_on", models.DateTimeField(auto_now_add=True)),
                ("updated_on", models.DateTimeField(auto_now=True)),
                (
                    "iro",
                    models.ForeignKey(
                        db_column="iro_id",
                        on_delete=django.db.models.deletion.CASCADE,
                        to="assessments.iro",
                    ),
                ),
                (
                    "iro_version",
                    models.ForeignKey(
                        blank=True,
                        db_column="iro_version_id",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="assessments.iroversion",
                    ),
                ),
                (
                    "tenant",
                    models.ForeignKey(
                        db_column="tenant_id",
                        on_delete=django.db.models.deletion.CASCADE,
                        to="tenants.tenantconfig",
                    ),
                ),
            ],
            options={
                "db_table": "review",
            },
        ),
        migrations.CreateModel(
            name="Signoff",
            fields=[
                ("signoff_id", models.AutoField(primary_key=True, serialize=False)),
                ("signed_by", models.IntegerField()),
                ("signed_on", models.DateTimeField(auto_now_add=True)),
                (
                    "signature_ref",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                ("comments", models.TextField(blank=True, default="")),
                (
                    "iro_version",
                    models.ForeignKey(
                        blank=True,
                        db_column="iro_version_id",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="assessments.iroversion",
                    ),
                ),
                (
                    "review",
                    models.ForeignKey(
                        db_column="review_id",
                        on_delete=django.db.models.deletion.CASCADE,
                        to="assessments.review",
                    ),
                ),
                (
                    "tenant",
                    models.ForeignKey(
                        db_column="tenant_id",
                        on_delete=django.db.models.deletion.CASCADE,
                        to="tenants.tenantconfig",
                    ),
                ),
            ],
            options={
                "db_table": "signoff",
            },
        ),
        migrations.CreateModel(
            name="RiskOppAssessment",
            fields=[
                (
                    "risk_opp_assessment_id",
                    models.AutoField(primary_key=True, serialize=False),
                ),
                (
                    "fin_materiality_def_version_id",
                    models.IntegerField(blank=True, null=True),
                ),
                ("time_horizon", models.CharField(max_length=20)),
                ("workforce_risk", models.IntegerField(blank=True, null=True)),
                ("workforce_risk_rationale", models.TextField(blank=True, null=True)),
                ("operational_risk", models.IntegerField(blank=True, null=True)),
                ("operational_risk_rationale", models.TextField(blank=True, null=True)),
                ("cost_of_capital_risk", models.IntegerField(blank=True, null=True)),
                (
                    "cost_of_capital_risk_rationale",
                    models.TextField(blank=True, null=True),
                ),
                ("reputational_risk", models.IntegerField(blank=True, null=True)),
                (
                    "reputational_risk_rationale",
                    models.TextField(blank=True, null=True),
                ),
                ("legal_compliance_risk", models.IntegerField(blank=True, null=True)),
                (
                    "legal_compliance_risk_rationale",
                    models.TextField(blank=True, null=True),
                ),
                ("likelihood_score", models.IntegerField(blank=True, null=True)),
                ("likelihood_rationale", models.TextField(blank=True, null=True)),
                (
                    "financial_magnitude_score",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=5, null=True
                    ),
                ),
                (
                    "financial_materiality_score",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=5, null=True
                    ),
                ),
                ("overall_rationale", models.TextField(blank=True, null=True)),
                ("related_documents", models.TextField(blank=True, null=True)),
                ("created_on", models.DateTimeField(auto_now_add=True)),
                ("updated_on", models.DateTimeField(auto_now=True)),
                (
                    "iro",
                    models.ForeignKey(
                        db_column="iro_id",
                        on_delete=django.db.models.deletion.CASCADE,
                        to="assessments.iro",
                    ),
                ),
                (
                    "tenant",
                    models.ForeignKey(
                        db_column="tenant_id",
                        on_delete=django.db.models.deletion.CASCADE,
                        to="tenants.tenantconfig",
                    ),
                ),
            ],
            options={
                "db_table": "risk_opp_assessment",
            },
        ),
        migrations.CreateModel(
            name="IRORelationship",
            fields=[
                (
                    "relationship_id",
                    models.AutoField(primary_key=True, serialize=False),
                ),
                ("relationship_type", models.CharField(max_length=50)),
                ("created_on", models.DateTimeField(auto_now_add=True)),
                ("created_by", models.IntegerField()),
                ("notes", models.TextField(blank=True, null=True)),
                (
                    "source_iro",
                    models.ForeignKey(
                        db_column="source_iro_id",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="source_relationships",
                        to="assessments.iro",
                    ),
                ),
                (
                    "target_iro",
                    models.ForeignKey(
                        db_column="target_iro_id",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="target_relationships",
                        to="assessments.iro",
                    ),
                ),
                (
                    "tenant",
                    models.ForeignKey(
                        db_column="tenant_id",
                        on_delete=django.db.models.deletion.CASCADE,
                        to="tenants.tenantconfig",
                    ),
                ),
            ],
            options={
                "db_table": "iro_relationship",
            },
        ),
        migrations.CreateModel(
            name="ImpactMaterialityDef",
            fields=[
                ("def_id", models.AutoField(primary_key=True, serialize=False)),
                ("version_num", models.IntegerField()),
                ("dimension", models.CharField(max_length=50)),
                ("score_value", models.IntegerField()),
                ("definition_text", models.TextField()),
                ("valid_from", models.DateTimeField()),
                ("valid_to", models.DateTimeField(blank=True, null=True)),
                ("created_on", models.DateTimeField(auto_now_add=True)),
                ("created_by", models.IntegerField()),
                (
                    "tenant",
                    models.ForeignKey(
                        db_column="tenant_id",
                        on_delete=django.db.models.deletion.CASCADE,
                        to="tenants.tenantconfig",
                    ),
                ),
            ],
            options={
                "db_table": "impact_materiality_def",
            },
        ),
        migrations.CreateModel(
            name="ImpactAssessment",
            fields=[
                (
                    "impact_assessment_id",
                    models.AutoField(primary_key=True, serialize=False),
                ),
                (
                    "impact_materiality_def_version_id",
                    models.IntegerField(blank=True, null=True),
                ),
                ("time_horizon", models.CharField(max_length=20)),
                (
                    "actual_or_potential",
                    models.CharField(blank=True, max_length=50, null=True),
                ),
                (
                    "related_to_human_rights",
                    models.CharField(blank=True, max_length=50, null=True),
                ),
                ("scale_score", models.IntegerField(blank=True, null=True)),
                ("scale_rationale", models.TextField(blank=True, null=True)),
                ("scope_score", models.IntegerField(blank=True, null=True)),
                ("scope_rationale", models.TextField(blank=True, null=True)),
                ("irremediability_score", models.IntegerField(blank=True, null=True)),
                ("irremediability_rationale", models.TextField(blank=True, null=True)),
                ("likelihood_score", models.IntegerField(blank=True, null=True)),
                ("likelihood_rationale", models.TextField(blank=True, null=True)),
                (
                    "severity_score",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=5, null=True
                    ),
                ),
                (
                    "impact_materiality_score",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=5, null=True
                    ),
                ),
                ("overall_rationale", models.TextField(blank=True, null=True)),
                ("related_documents", models.TextField(blank=True, null=True)),
                ("created_on", models.DateTimeField(auto_now_add=True)),
                ("updated_on", models.DateTimeField(auto_now=True)),
                (
                    "iro",
                    models.ForeignKey(
                        db_column="iro_id",
                        on_delete=django.db.models.deletion.CASCADE,
                        to="assessments.iro",
                    ),
                ),
                (
                    "tenant",
                    models.ForeignKey(
                        db_column="tenant_id",
                        on_delete=django.db.models.deletion.CASCADE,
                        to="tenants.tenantconfig",
                    ),
                ),
            ],
            options={
                "db_table": "impact_assessment",
            },
        ),
        migrations.CreateModel(
            name="FinMaterialityWeights",
            fields=[
                ("weight_id", models.AutoField(primary_key=True, serialize=False)),
                ("version_num", models.IntegerField()),
                ("dimension", models.CharField(max_length=50)),
                ("weight", models.DecimalField(decimal_places=2, max_digits=5)),
                ("valid_from", models.DateTimeField()),
                ("valid_to", models.DateTimeField(blank=True, null=True)),
                ("created_on", models.DateTimeField(auto_now_add=True)),
                ("created_by", models.IntegerField()),
                (
                    "tenant",
                    models.ForeignKey(
                        db_column="tenant_id",
                        on_delete=django.db.models.deletion.CASCADE,
                        to="tenants.tenantconfig",
                    ),
                ),
            ],
            options={
                "db_table": "fin_materiality_weights",
            },
        ),
        migrations.CreateModel(
            name="FinMaterialityMagnitudeDef",
            fields=[
                ("def_id", models.AutoField(primary_key=True, serialize=False)),
                ("version_num", models.IntegerField()),
                ("score_value", models.IntegerField()),
                ("definition_text", models.TextField()),
                ("valid_from", models.DateTimeField()),
                ("valid_to", models.DateTimeField(blank=True, null=True)),
                ("created_on", models.DateTimeField(auto_now_add=True)),
                ("created_by", models.IntegerField()),
                (
                    "tenant",
                    models.ForeignKey(
                        db_column="tenant_id",
                        on_delete=django.db.models.deletion.CASCADE,
                        to="tenants.tenantconfig",
                    ),
                ),
            ],
            options={
                "db_table": "fin_materiality_magnitude_def",
            },
        ),
        migrations.CreateModel(
            name="AuditTrail",
            fields=[
                ("audit_id", models.AutoField(primary_key=True, serialize=False)),
                ("entity_type", models.CharField(max_length=50)),
                ("entity_id", models.IntegerField()),
                ("action", models.CharField(max_length=50)),
                ("user_id", models.IntegerField()),
                ("timestamp", models.DateTimeField(auto_now_add=True)),
                ("data_diff", models.JSONField(default=dict)),
                (
                    "tenant",
                    models.ForeignKey(
                        db_column="tenant_id",
                        on_delete=django.db.models.deletion.CASCADE,
                        to="tenants.tenantconfig",
                    ),
                ),
            ],
            options={
                "db_table": "audit_trail",
            },
        ),
    ]

</file>

<file path='apps/assessments/migrations/0002_assessment_tenant.py'>
# Generated by Django 4.2 on 2025-02-26 16:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0001_initial'),
        ('assessments', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='assessment',
            name='tenant',
            field=models.ForeignKey(db_column='tenant_id', default=1, on_delete=django.db.models.deletion.CASCADE, to='tenants.tenantconfig'),
            preserve_default=False,
        ),
    ]

</file>

<file path='apps/assessments/migrations/0003_alter_assessment_tenant.py'>
# Generated by Django 4.2 on 2025-02-26 16:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0001_initial'),
        ('assessments', '0002_assessment_tenant'),
    ]

    operations = [
        migrations.AlterField(
            model_name='assessment',
            name='tenant',
            field=models.ForeignKey(blank=True, db_column='tenant_id', null=True, on_delete=django.db.models.deletion.CASCADE, to='tenants.tenantconfig'),
        ),
    ]

</file>

<file path='apps/assessments/migrations/__init__.py'>

</file>

<file path='apps/assessments/models.py'>
# apps/assessments/models.py

from django.db import models
from tenants.models import TenantConfig


class Assessment(models.Model):
    """
    (Kept from your original code, in case you still need a top-level
     Assessment model. You can remove it if it's no longer used.)
    """
    tenant = models.ForeignKey(TenantConfig, on_delete=models.CASCADE, db_column="tenant_id", null=True, blank=True)
    name = models.CharField(max_length=200, help_text="Name of the assessment")
    description = models.TextField(blank=True, help_text="Optional description")
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        # This table also goes into each tenant schema if you want it that way. 
        db_table = 'assessment'


class IRO(models.Model):
    iro_id = models.AutoField(primary_key=True)
    tenant = models.ForeignKey(TenantConfig, on_delete=models.CASCADE, db_column="tenant_id")
    current_version_id = models.IntegerField(null=True, blank=True)
    current_stage = models.CharField(max_length=50, default='Draft')
    type = models.CharField(max_length=20)
    source_of_iro = models.CharField(max_length=255, null=True, blank=True)
    esrs_standard = models.CharField(max_length=100, null=True, blank=True)
    last_assessment_date = models.DateTimeField(null=True, blank=True)
    assessment_count = models.IntegerField(default=0)
    last_assessment_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'iro'
    
    @property
    def title(self):
        """Return the title from the current version of this IRO"""
        if self.current_version_id:
            try:
                version = IROVersion.objects.get(version_id=self.current_version_id)
                return version.title
            except IROVersion.DoesNotExist:
                pass
        
        # Fallback: try to get the latest version's title
        latest_version = IROVersion.objects.filter(iro=self).order_by('-version_number').first()
        if latest_version:
            return latest_version.title
        
        return f"IRO #{self.iro_id}"  # Fallback title
    
    @property
    def description(self):
        """Return the description from the current version of this IRO"""
        if self.current_version_id:
            try:
                version = IROVersion.objects.get(version_id=self.current_version_id)
                return version.description
            except IROVersion.DoesNotExist:
                pass
                
        # Fallback: try to get the latest version's description
        latest_version = IROVersion.objects.filter(iro=self).order_by('-version_number').first()
        if latest_version:
            return latest_version.description
            
        return ""  # Fallback description



class IROVersion(models.Model):
    version_id = models.AutoField(primary_key=True)
    iro = models.ForeignKey(IRO, on_delete=models.CASCADE, db_column="iro_id")
    tenant = models.ForeignKey(TenantConfig, on_delete=models.CASCADE, db_column="tenant_id")
    version_number = models.IntegerField()
    title = models.CharField(max_length=255)
    description = models.TextField()
    sust_topic_level1 = models.CharField(max_length=100, null=True, blank=True)
    sust_topic_level2 = models.CharField(max_length=100, null=True, blank=True)
    sust_topic_level3 = models.CharField(max_length=100, null=True, blank=True)
    value_chain_lv1 = models.JSONField(default=list)  # or ArrayField in Postgres
    value_chain_lv2 = models.JSONField(default=list)
    economic_activity = models.JSONField(default=list)
    status = models.CharField(max_length=50, default='Draft')
    created_by = models.IntegerField()
    created_on = models.DateTimeField(auto_now_add=True)
    parent_version_id = models.IntegerField(null=True, blank=True)
    split_type = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = 'iro_version'


class IRORelationship(models.Model):
    relationship_id = models.AutoField(primary_key=True)
    tenant = models.ForeignKey(TenantConfig, on_delete=models.CASCADE, db_column="tenant_id")
    source_iro = models.ForeignKey(IRO, on_delete=models.CASCADE, db_column="source_iro_id",
                                   related_name='source_relationships')
    target_iro = models.ForeignKey(IRO, on_delete=models.CASCADE, db_column="target_iro_id",
                                   related_name='target_relationships')
    relationship_type = models.CharField(max_length=50)
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.IntegerField()
    notes = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'iro_relationship'


class ImpactAssessment(models.Model):
    impact_assessment_id = models.AutoField(primary_key=True)
    iro = models.ForeignKey(IRO, on_delete=models.CASCADE, db_column="iro_id")
    tenant = models.ForeignKey(TenantConfig, on_delete=models.CASCADE, db_column="tenant_id")
    impact_materiality_def_version_id = models.IntegerField(null=True, blank=True)
    time_horizon = models.CharField(max_length=20)
    actual_or_potential = models.CharField(max_length=50, null=True, blank=True)
    related_to_human_rights = models.CharField(max_length=50, null=True, blank=True)
    scale_score = models.IntegerField(null=True, blank=True)
    scale_rationale = models.TextField(null=True, blank=True)
    scope_score = models.IntegerField(null=True, blank=True)
    scope_rationale = models.TextField(null=True, blank=True)
    irremediability_score = models.IntegerField(null=True, blank=True)
    irremediability_rationale = models.TextField(null=True, blank=True)
    likelihood_score = models.IntegerField(null=True, blank=True)
    likelihood_rationale = models.TextField(null=True, blank=True)
    severity_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    impact_materiality_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    overall_rationale = models.TextField(null=True, blank=True)
    related_documents = models.TextField(null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'impact_assessment'


class RiskOppAssessment(models.Model):
    risk_opp_assessment_id = models.AutoField(primary_key=True)
    iro = models.ForeignKey(IRO, on_delete=models.CASCADE, db_column="iro_id")
    tenant = models.ForeignKey(TenantConfig, on_delete=models.CASCADE, db_column="tenant_id")
    fin_materiality_def_version_id = models.IntegerField(null=True, blank=True)
    time_horizon = models.CharField(max_length=20)
    workforce_risk = models.IntegerField(null=True, blank=True)
    workforce_risk_rationale = models.TextField(null=True, blank=True)
    operational_risk = models.IntegerField(null=True, blank=True)
    operational_risk_rationale = models.TextField(null=True, blank=True)
    cost_of_capital_risk = models.IntegerField(null=True, blank=True)
    cost_of_capital_risk_rationale = models.TextField(null=True, blank=True)
    reputational_risk = models.IntegerField(null=True, blank=True)
    reputational_risk_rationale = models.TextField(null=True, blank=True)
    legal_compliance_risk = models.IntegerField(null=True, blank=True)
    legal_compliance_risk_rationale = models.TextField(null=True, blank=True)
    likelihood_score = models.IntegerField(null=True, blank=True)
    likelihood_rationale = models.TextField(null=True, blank=True)
    financial_magnitude_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    financial_materiality_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    overall_rationale = models.TextField(null=True, blank=True)
    related_documents = models.TextField(null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'risk_opp_assessment'


class Review(models.Model):
    review_id = models.AutoField(primary_key=True)
    iro = models.ForeignKey(IRO, on_delete=models.CASCADE, db_column="iro_id")
    tenant = models.ForeignKey(TenantConfig, on_delete=models.CASCADE, db_column="tenant_id")
    iro_version = models.ForeignKey(IROVersion, on_delete=models.SET_NULL, db_column="iro_version_id",
                                    null=True, blank=True)
    reviewer_id = models.IntegerField()
    status = models.CharField(max_length=50, default='Draft')
    notes = models.TextField(default='', blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'review'


class Signoff(models.Model):
    signoff_id = models.AutoField(primary_key=True)
    review = models.ForeignKey(Review, on_delete=models.CASCADE, db_column="review_id")
    tenant = models.ForeignKey(TenantConfig, on_delete=models.CASCADE, db_column="tenant_id")
    iro_version = models.ForeignKey(IROVersion, on_delete=models.SET_NULL, db_column="iro_version_id",
                                    null=True, blank=True)
    signed_by = models.IntegerField()
    signed_on = models.DateTimeField(auto_now_add=True)
    signature_ref = models.CharField(max_length=255, null=True, blank=True)
    comments = models.TextField(default='', blank=True)

    class Meta:
        db_table = 'signoff'


class AuditTrail(models.Model):
    audit_id = models.AutoField(primary_key=True)
    tenant = models.ForeignKey(TenantConfig, on_delete=models.CASCADE, db_column="tenant_id")
    entity_type = models.CharField(max_length=50)
    entity_id = models.IntegerField()
    action = models.CharField(max_length=50)
    user_id = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
    data_diff = models.JSONField(default=dict)

    class Meta:
        db_table = 'audit_trail'


class ImpactMaterialityDef(models.Model):
    def_id = models.AutoField(primary_key=True)
    tenant = models.ForeignKey(TenantConfig, on_delete=models.CASCADE, db_column="tenant_id")
    version_num = models.IntegerField()
    dimension = models.CharField(max_length=50)
    score_value = models.IntegerField()
    definition_text = models.TextField()
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField(null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.IntegerField()

    class Meta:
        db_table = 'impact_materiality_def'


class FinMaterialityWeights(models.Model):
    weight_id = models.AutoField(primary_key=True)
    tenant = models.ForeignKey(TenantConfig, on_delete=models.CASCADE, db_column="tenant_id")
    version_num = models.IntegerField()
    dimension = models.CharField(max_length=50)
    weight = models.DecimalField(max_digits=5, decimal_places=2)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField(null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.IntegerField()

    class Meta:
        db_table = 'fin_materiality_weights'


class FinMaterialityMagnitudeDef(models.Model):
    def_id = models.AutoField(primary_key=True)
    tenant = models.ForeignKey(TenantConfig, on_delete=models.CASCADE, db_column="tenant_id")
    version_num = models.IntegerField()
    score_value = models.IntegerField()
    definition_text = models.TextField()
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField(null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.IntegerField()

    class Meta:
        db_table = 'fin_materiality_magnitude_def'
</file>

<file path='apps/assessments/tasks.py'>
# apps/assessments/tasks.py
from celery import shared_task

@shared_task
def example_task(assessment_id):
    # your asynchronous logic, e.g., sending an email after an assessment is created
    pass
</file>

<file path='apps/assessments/templatetags/__init__.py'>

</file>

<file path='apps/assessments/templatetags/assessment_filters.py'>
from django import template

register = template.Library()

@register.filter(name='mul')
def mul(value, arg):
    """Multiply the value by the argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return ''

</file>

<file path='apps/assessments/urls.py'>
# apps/assessments/urls.py
from django.urls import path
from .views import (
    AssessmentListView, AssessmentCreateView, AssessmentUpdateView,
    IROListView, IROCreateView, IROUpdateView
)

app_name = 'assessments'

urlpatterns = [
    path('', AssessmentListView.as_view(), name='list'),
    path('create/', AssessmentCreateView.as_view(), name='create'),
    path('<int:pk>/edit/', AssessmentUpdateView.as_view(), name='edit'),

    # IRO CRUD
    path('iro/', IROListView.as_view(), name='iro-list'),
    path('iro/create/', IROCreateView.as_view(), name='iro-create'),
    path('iro/<int:pk>/edit/', IROUpdateView.as_view(), name='iro-edit'),
]
</file>

<file path='apps/assessments/views.py'>
# apps/assessments/views.py
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django import forms
from .models import Assessment, IRO
from tenants.models import TenantConfig

class ContextMixin:
    """
    Mixin to add context-aware functionality to views.
    
    Adds context_data to the template context, including:
    - available_tenants: List of available tenants
    - available_assessments: List of available assessments
    - available_iros: List of available IROs
    
    Additionally sets up filtering based on the current context.
    """
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add context selectors data
        if self.request.user.is_staff:
            context['available_tenants'] = TenantConfig.objects.all()
        
        # Filter assessments by tenant if a tenant is selected
        tenant = self.request.context.get('tenant')
        try:
            if tenant:
                context['available_assessments'] = Assessment.objects.filter(tenant=tenant)
            else:
                context['available_assessments'] = Assessment.objects.all()
        except Exception as e:
            # Fallback if filtering fails (e.g., missing tenant field)
            context['available_assessments'] = Assessment.objects.all()
        
        # Filter IROs by assessment if an assessment is selected
        assessment = self.request.context.get('assessment')
        try:
            if assessment:
                # Assuming IROs can be linked to assessments
                # Adjust this query based on your actual data model
                context['available_iros'] = IRO.objects.filter(assessment=assessment)
            elif tenant:
                # If only tenant is selected, show all IROs for that tenant
                context['available_iros'] = IRO.objects.filter(tenant=tenant)
            else:
                context['available_iros'] = IRO.objects.all()
        except Exception as e:
            # Fallback if filtering fails
            context['available_iros'] = IRO.objects.all()
            
        return context
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        try:
            # Filter by tenant
            tenant = self.request.context.get('tenant')
            if tenant and hasattr(self.model, 'tenant'):
                queryset = queryset.filter(tenant=tenant)
            
            # Filter by assessment
            assessment = self.request.context.get('assessment')
            if assessment and hasattr(self.model, 'assessment'):
                queryset = queryset.filter(assessment=assessment)
            
            # Filter by IRO
            iro = self.request.context.get('iro')
            if iro and hasattr(self.model, 'iro'):
                queryset = queryset.filter(iro=iro)
        except Exception as e:
            # If any filtering fails, return the original queryset
            pass
            
        return queryset


########################
# Existing CBVs for Assessment
########################

class AssessmentListView(ContextMixin, ListView):
    model = Assessment
    template_name = 'assessments/assessment_list.html'
    context_object_name = 'assessments'


class AssessmentCreateView(ContextMixin, CreateView):
    model = Assessment
    fields = ['name', 'description']
    template_name = 'assessments/assessment_form.html'
    success_url = reverse_lazy('assessments:list')


class AssessmentUpdateView(ContextMixin, UpdateView):
    model = Assessment
    fields = ['name', 'description']
    template_name = 'assessments/assessment_form.html'
    success_url = reverse_lazy('assessments:list')


########################
# New: IRO CRUD Views
########################

class IROForm(forms.ModelForm):
    """Example usage of django-crispy-forms (optional). 
       Just ensure you have 'crispy_forms' in INSTALLED_APPS and 
       installed the library via pip."""
    class Meta:
        model = IRO
        fields = [
            'tenant',
            'type',
            'source_of_iro',
            'esrs_standard',
            'current_stage',
            'last_assessment_date',
        ]

class IROListView(ContextMixin, ListView):
    model = IRO
    template_name = 'assessments/iro_list.html'
    context_object_name = 'iros'


class IROCreateView(ContextMixin, CreateView):
    model = IRO
    form_class = IROForm
    template_name = 'assessments/iro_form.html'
    success_url = reverse_lazy('assessments:iro-list')


class IROUpdateView(ContextMixin, UpdateView):
    model = IRO
    form_class = IROForm
    template_name = 'assessments/iro_form.html'
    success_url = reverse_lazy('assessments:iro-list')
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

<file path='core/middleware/__init__.py'>

</file>

<file path='core/middleware/context_middleware.py'>
from django.urls import resolve
from tenants.models import TenantConfig
from apps.assessments.models import Assessment, IRO

class ContextMiddleware:
    """
    Middleware to manage hierarchical context:
    - tenant (company)
    - assessment (first time vs refresh)
    - IRO (specific IRO being assessed)
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Initialize context attributes
        request.context = {
            'tenant': None,
            'assessment': None,
            'iro': None
        }

        # Check for tenant in session first (manually selected tenant)
        if 'tenant_id' in request.session:
            try:
                tenant_id = request.session['tenant_id']
                tenant = TenantConfig.objects.get(tenant_id=tenant_id)
                request.context['tenant'] = tenant
            except TenantConfig.DoesNotExist:
                # Clear invalid tenant from session
                if 'tenant_id' in request.session:
                    del request.session['tenant_id']
        # Fallback to request.tenant (set by django-tenants based on domain)
        elif hasattr(request, 'tenant'):
            request.context['tenant'] = request.tenant

        # Check session for stored context values
        if 'assessment_id' in request.session:
            try:
                assessment_id = request.session['assessment_id']
                request.context['assessment'] = Assessment.objects.get(id=assessment_id)
            except Assessment.DoesNotExist:
                # Clear invalid context
                if 'assessment_id' in request.session:
                    del request.session['assessment_id']

        if 'iro_id' in request.session:
            try:
                iro_id = request.session['iro_id']
                request.context['iro'] = IRO.objects.get(iro_id=iro_id)
            except IRO.DoesNotExist:
                # Clear invalid context
                if 'iro_id' in request.session:
                    del request.session['iro_id']

        # Check URL parameters for context overrides
        # Safely check if user is authenticated and staff
        is_staff = hasattr(request, 'user') and request.user.is_authenticated and request.user.is_staff
        
        if 'tenant_id' in request.GET and is_staff:
            try:
                tenant_id = int(request.GET.get('tenant_id'))
                tenant = TenantConfig.objects.get(tenant_id=tenant_id)
                request.context['tenant'] = tenant
                request.session['tenant_id'] = tenant_id
            except (ValueError, TenantConfig.DoesNotExist):
                pass

        if 'assessment_id' in request.GET:
            try:
                assessment_id = int(request.GET.get('assessment_id'))
                assessment = Assessment.objects.get(id=assessment_id)
                request.context['assessment'] = assessment
                request.session['assessment_id'] = assessment_id
            except (ValueError, Assessment.DoesNotExist):
                pass

        if 'iro_id' in request.GET:
            try:
                iro_id = int(request.GET.get('iro_id'))
                iro = IRO.objects.get(iro_id=iro_id)
                request.context['iro'] = iro
                request.session['iro_id'] = iro_id
            except (ValueError, IRO.DoesNotExist):
                pass

        # Process the request
        response = self.get_response(request)
        return response
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
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',  # Authentication must run BEFORE our middleware
    'core.middleware.context_middleware.ContextMiddleware',     # Now placed after authentication
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

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Example Celery or other global settings can remain here
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
</file>

<file path='core/settings/local.py'>
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

# Any additional local-only settings or logging can remain here
</file>

<file path='core/settings/production.py'>
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
</file>

<file path='core/urls.py'>
# core/urls.py - Update the home URL pattern

from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from . import views

urlpatterns = [
    # Replace this line:
    # path('', TemplateView.as_view(template_name='home.html'), name='home'),
    # With this:
    path('', views.home_dashboard, name='home'),
    
    # Keep the rest of the URL patterns the same
    path('admin/', admin.site.urls),
    path('assessments/', include('apps.assessments.urls')),
    path('tenants/', include('tenants.urls', namespace='tenants')),
    path('api/assessments/', include('apps.assessments.api.urls')),  
    path('api/tenants/', include('tenants.api.urls')), 
    path('set-context/', views.set_context, name='set_context'),
]
</file>

<file path='core/views.py'>
# core/views.py
from django.http import JsonResponse
from django.shortcuts import redirect
from django.views.decorators.http import require_GET
from tenants.models import TenantConfig
from apps.assessments.models import Assessment, IRO
from django.shortcuts import render
from django.db.models import Count, Avg, Q
from apps.assessments.models import IRO, ImpactAssessment, RiskOppAssessment, AuditTrail, Review
import json

def home_dashboard(request):
    # Get tenant from context middleware
    tenant = request.context.get('tenant')
    
    # Base queryset - filter by tenant if one is selected
    iro_queryset = IRO.objects.all()
    if tenant:
        iro_queryset = iro_queryset.filter(tenant=tenant)
    
    # Calculate metrics for dashboard
    total_iros = iro_queryset.count()
    
    # Define high materiality as IROs with score > 3.5
    high_materiality_count = iro_queryset.filter(last_assessment_score__gt=3.5).count()
    
    # Count pending reviews
    pending_reviews_count = Review.objects.filter(status='In_Review')
    if tenant:
        pending_reviews_count = pending_reviews_count.filter(tenant=tenant)
    pending_reviews_count = pending_reviews_count.count()
    
    # Count completed assessments (approved)
    completed_assessments_count = iro_queryset.filter(current_stage='Approved').count()
    
    # Get recent activity from audit trail
    recent_activities = AuditTrail.objects.all().order_by('-timestamp')[:5]
    
    # Process activities to add color and icon information
    activity_data = []
    for activity in recent_activities:
        activity_info = {
            'timestamp': activity.timestamp,
            'action': activity.action,
            'description': f"{activity.entity_type} #{activity.entity_id} {activity.action}",
        }
        
        # Set icon and color based on action type
        if activity.action == 'created':
            activity_info['icon'] = 'plus'
            activity_info['icon_color'] = 'info'
        elif activity.action == 'updated':
            activity_info['icon'] = 'edit'
            activity_info['icon_color'] = 'warning'
        elif activity.action == 'approved':
            activity_info['icon'] = 'check'
            activity_info['icon_color'] = 'success'
        elif activity.action == 'deleted':
            activity_info['icon'] = 'trash'
            activity_info['icon_color'] = 'danger'
        else:
            activity_info['icon'] = 'clipboard-list'
            activity_info['icon_color'] = 'primary'
            
        activity_data.append(activity_info)
    
    # Get high priority IROs (highest scores)
    high_priority_iros = []
    for iro in iro_queryset.order_by('-last_assessment_score')[:10]:
        # Get the latest impact and financial scores
        impact_assessments = ImpactAssessment.objects.filter(iro=iro).order_by('-created_on')
        risk_opp_assessments = RiskOppAssessment.objects.filter(iro=iro).order_by('-created_on')
        
        impact_score = impact_assessments.first().impact_materiality_score if impact_assessments.exists() else 0.0
        financial_score = risk_opp_assessments.first().financial_materiality_score if risk_opp_assessments.exists() else 0.0
        
        high_priority_iros.append({
            'iro_id': iro.iro_id,
            'title': iro.title,
            'type': iro.type,
            'impact_score': impact_score,
            'financial_score': financial_score,
            'current_stage': iro.current_stage,
        })
    
    # Prepare data for materiality matrix
    matrix_data = []
    for iro in iro_queryset:
        impact_assessment = ImpactAssessment.objects.filter(iro=iro).order_by('-created_on').first()
        risk_opp_assessment = RiskOppAssessment.objects.filter(iro=iro).order_by('-created_on').first()
        
        if impact_assessment and risk_opp_assessment:
            matrix_data.append({
                'id': iro.iro_id,
                'title': iro.title,
                'type': iro.type,
                'impact_score': float(impact_assessment.impact_materiality_score or 0),
                'financial_score': float(risk_opp_assessment.financial_materiality_score or 0),
            })
    
    context = {
        'total_iros': total_iros,
        'high_materiality_count': high_materiality_count,
        'pending_reviews_count': pending_reviews_count,
        'completed_assessments_count': completed_assessments_count,
        'recent_activities': activity_data,
        'high_priority_iros': high_priority_iros,
        'materiality_matrix_data': json.dumps(matrix_data),
    }
    
    # Add available tenants to context for the tenant selector
    if request.user.is_staff:
        context['available_tenants'] = TenantConfig.objects.all()
    
    return render(request, 'home.html', context)

@require_GET
def set_context(request):
    """
    View to handle setting context values and redirecting.
    Can be called via AJAX or as a normal GET request.
    """
    redirect_url = request.GET.get('next', '/')
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    # Safely check if user is authenticated and staff
    is_staff = hasattr(request, 'user') and request.user.is_authenticated and request.user.is_staff
    
    # Check for tenant selection (admin only)
    if 'tenant_id' in request.GET and is_staff:
        try:
            tenant_id = int(request.GET.get('tenant_id'))
            tenant = TenantConfig.objects.get(tenant_id=tenant_id)
            request.session['tenant_id'] = tenant_id
        except (ValueError, TenantConfig.DoesNotExist):
            pass
    
    
    # Check for assessment selection
    if 'assessment_id' in request.GET:
        try:
            assessment_id = int(request.GET.get('assessment_id'))
            assessment = Assessment.objects.get(id=assessment_id)
            request.session['assessment_id'] = assessment_id
            # Clear IRO when assessment changes
            if 'iro_id' in request.session:
                del request.session['iro_id']
        except (ValueError, Assessment.DoesNotExist):
            pass
    
    # Check for IRO selection
    if 'iro_id' in request.GET:
        try:
            iro_id = int(request.GET.get('iro_id'))
            iro = IRO.objects.get(iro_id=iro_id)
            request.session['iro_id'] = iro_id
        except (ValueError, IRO.DoesNotExist):
            pass
    
    if is_ajax:
        # For AJAX requests, return updated context as JSON
        context = {
            'tenant': None,
            'assessment': None,
            'iro': None
        }
        
        # Populate context based on session values
        if 'tenant_id' in request.session:
            try:
                tenant = TenantConfig.objects.get(tenant_id=request.session['tenant_id'])
                context['tenant'] = {
                    'tenant_id': tenant.tenant_id,
                    'tenant_name': tenant.tenant_name
                }
            except TenantConfig.DoesNotExist:
                pass
        
        if 'assessment_id' in request.session:
            try:
                assessment = Assessment.objects.get(id=request.session['assessment_id'])
                context['assessment'] = {
                    'id': assessment.id,
                    'name': assessment.name,
                    'description': assessment.description
                }
            except Assessment.DoesNotExist:
                pass
        
        if 'iro_id' in request.session:
            try:
                iro = IRO.objects.get(iro_id=request.session['iro_id'])
                context['iro'] = {
                    'iro_id': iro.iro_id,
                    'title': iro.title if hasattr(iro, 'title') else f"IRO #{iro.iro_id}",
                    'type': iro.type
                }
            except IRO.DoesNotExist:
                pass
        
        return JsonResponse({
            'success': True,
            'context': context,
            'redirect_url': redirect_url if request.GET.get('reload', False) else None
        })
    else:
        # For non-AJAX requests, redirect to the specified next URL
        return redirect(redirect_url)
</file>

<file path='core/wsgi.py'>
# core/wsgi.py
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.local')

application = get_wsgi_application()
</file>

<file path='docker-compose.yaml'>
services:
  web:
    build: .
    command: >
      sh -c "
        until pg_isready -h db -p 5432 -U dma_user; do 
          echo 'Waiting for database...'; 
          sleep 2; 
        done;
        # Optional but recommended to include the tenants app in makemigrations:
        python manage.py makemigrations tenants;
        python manage.py makemigrations;

        # 1) Migrate shared schema
        python manage.py migrate_schemas --shared;

        # 2) Create or update the default tenant
        python manage.py init_tenant --name=default --domain=localhost;

        # 3) Migrate the tenant schemas
        python manage.py migrate_schemas --tenant;
        
        # 4) Initialize sample data for testing
        python manage.py init_sample_data;
        
        # Check if tenant schemas have the iro table after migration
        echo 'Listing tables in tenant_tenant1 schema...'
        PGPASSWORD=password psql -h db -U dma_user -d dma_db -c \"\\dt tenant_tenant1.*\"
        echo 'Listing tables in tenant_tenant2 schema...'
        PGPASSWORD=password psql -h db -U dma_user -d dma_db -c \"\\dt tenant_tenant2.*\"

        # 5) Collect static files so admin CSS/JS are available
        python manage.py collectstatic --noinput;

        # Finally start Gunicorn
        gunicorn core.wsgi:application --bind 0.0.0.0:8000
      "
    volumes:
      - .:/app
    ports:
      - "8000:8000"
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

  db:
    image: postgres:14
    restart: always
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts:/docker-entrypoint-initdb.d
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
    user: appuser  # Use the non-root user
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
            "available on your PYTHONPATH environment variable. "
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
django-tenants==3.5.0
django-crispy-forms==2.3
djangorestframework==3.14
crispy-bootstrap5==0.7
django-guardian==2.4.0

</file>

<file path='run_local.sh'>
#!/usr/bin/env bash

# run_local.sh
# Run this any time you need to rebuild or re-init the local environment.

# Exit on error
set -e

echo "Building Docker images..."
docker compose down
docker compose build

echo "Starting containers in the background..."
docker compose up -d

# Wait a few seconds to ensure the web container is fully started
echo "Waiting for the web container to finish startup..."
sleep 5

# First check if migrations are needed
echo "Checking if migrations are needed..."
if ! docker compose exec -T web python manage.py makemigrations --check; then
    echo "Migrations are needed. Creating migrations with default value for tenant field..."
    # Simulate selecting option 1 (one-off default) and providing default value 1
    docker compose exec -T web bash -c "echo -e \"1\n1\n\" | python manage.py makemigrations assessments"
else
    echo "No migrations needed."
fi

echo "Running shared migrations..."
docker compose exec -T web python manage.py migrate_schemas --shared

echo "Creating or updating default tenant..."
docker compose exec -T web python manage.py init_tenant --name=default --domain=localhost

echo "Running tenant migrations..."
docker compose exec -T web python manage.py migrate_schemas --tenant

echo "Prepopulating sample data (2 tenants, each with 5 IROs fully assessed)..."
docker compose exec -T web python manage.py init_sample_data

echo "Tailing logs. Press Ctrl+C to stop."
docker compose logs -f
</file>

<file path='scripts/01-init-schemas.sql'>
--
-- 01-init-schemas.sql
--

-- Define the create_tenant_schema function without trying to create public.tenant_config
-- or referencing its tenant_id field via foreign keys. 
-- If you invoke create_tenant_schema('some_tenant') manually, 
-- it will create the schema and the tenant-specific tables only.
--

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
            updated_on TIMESTAMP NOT NULL DEFAULT NOW()
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
            split_type VARCHAR(50)
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
            notes TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_iro_relationship_tenant_id ON %I.iro_relationship (tenant_id);
        CREATE INDEX IF NOT EXISTS idx_iro_relationship_src_tgt   ON %I.iro_relationship (source_iro_id, target_iro_id);
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
            updated_on TIMESTAMP NOT NULL DEFAULT NOW()
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
            updated_on TIMESTAMP NOT NULL DEFAULT NOW()
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
            updated_on TIMESTAMP NOT NULL DEFAULT NOW()
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
            comments TEXT NOT NULL DEFAULT ''
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
            data_diff JSONB NOT NULL DEFAULT '{}'
        );
        CREATE INDEX IF NOT EXISTS idx_audit_trail_tenant_id      ON %I.audit_trail (tenant_id);
        CREATE INDEX IF NOT EXISTS idx_audit_trail_entity_type_id ON %I.audit_trail (entity_type, entity_id);
        CREATE INDEX IF NOT EXISTS idx_audit_trail_timestamp      ON %I.audit_trail (timestamp);
    $f$, schema_name, schema_name, schema_name, schema_name);

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
            created_by INT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_imp_mat_def_tenant_id   ON %I.impact_materiality_def (tenant_id);
        CREATE INDEX IF NOT EXISTS idx_imp_mat_def_version_dim ON %I.impact_materiality_def (version_num, dimension);
    $f$, schema_name, schema_name, schema_name);

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
            created_by INT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_fin_weights_tenant_id   ON %I.fin_materiality_weights (tenant_id);
        CREATE INDEX IF NOT EXISTS idx_fin_weights_version_dim ON %I.fin_materiality_weights (version_num, dimension);
    $f$, schema_name, schema_name, schema_name);

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
            created_by INT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_fin_mag_def_tenant_id     ON %I.fin_materiality_magnitude_def (tenant_id);
        CREATE INDEX IF NOT EXISTS idx_fin_mag_def_version_score ON %I.fin_materiality_magnitude_def (version_num, score_value);
    $f$, schema_name, schema_name, schema_name);

END;
$$ LANGUAGE plpgsql;

-- NOTE: Removed any 'CREATE TABLE public.tenant_config' and 
-- any inserts or references that rely on public.tenant_config(tenant_id).
-- This script now only sets up tenant-side tables in each schema.
--
-- If you manually run:
--     SELECT create_tenant_schema('mytenant');
-- then the script above will create the 'tenant_mytenant' schema 
-- and all tenant-scope tables. 
--
-- Let Django run migrations to create and manage "public.tenant_config" itself.
</file>

<file path='static/js/context_manager.js'>
// static/js/context_manager.js

document.addEventListener('DOMContentLoaded', function() {
    // Function to update context display without reloading page
    function updateContextDisplay(contextData) {
        const tenantDisplay = document.getElementById('currentTenant');
        const assessmentDisplay = document.getElementById('currentAssessment');
        const iroDisplay = document.getElementById('currentIRO');
        
        if (tenantDisplay && contextData.tenant) {
            tenantDisplay.textContent = contextData.tenant.tenant_name;
            tenantDisplay.parentElement.classList.remove('text-muted');
        }
        
        if (assessmentDisplay) {
            if (contextData.assessment) {
                assessmentDisplay.textContent = contextData.assessment.name;
                assessmentDisplay.parentElement.classList.remove('text-muted');
            } else {
                assessmentDisplay.textContent = 'No assessment selected';
                assessmentDisplay.parentElement.classList.add('text-muted');
            }
        }
        
        if (iroDisplay) {
            if (contextData.iro) {
                iroDisplay.textContent = contextData.iro.title;
                iroDisplay.parentElement.classList.remove('text-muted');
                
                const iroBadge = document.getElementById('iroBadge');
                if (iroBadge) {
                    iroBadge.textContent = contextData.iro.type;
                    // Set badge color based on type
                    iroBadge.classList.remove('bg-danger', 'bg-success', 'bg-primary');
                    if (contextData.iro.type === 'Risk') {
                        iroBadge.classList.add('bg-danger');
                    } else if (contextData.iro.type === 'Opportunity') {
                        iroBadge.classList.add('bg-success');
                    } else {
                        iroBadge.classList.add('bg-primary');
                    }
                }
            } else {
                iroDisplay.textContent = 'No IRO selected';
                iroDisplay.parentElement.classList.add('text-muted');
            }
        }
    }
    
    // Handle context selection via Ajax
    const contextLinks = document.querySelectorAll('[data-context-link]');
    contextLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            const url = this.getAttribute('href');
            
            fetch(url, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    updateContextDisplay(data.context);
                    
                    // Close any open modals
                    const openModals = document.querySelectorAll('.modal.show');
                    openModals.forEach(modal => {
                        const modalInstance = bootstrap.Modal.getInstance(modal);
                        if (modalInstance) {
                            modalInstance.hide();
                        }
                    });
                    
                    // Optionally reload content sections
                    if (data.redirect_url) {
                        window.location.href = data.redirect_url;
                    }
                }
            })
            .catch(error => console.error('Error updating context:', error));
        });
    });
});
</file>

<file path='static/js/dashboard.js'>
// static/js/dashboard.js

document.addEventListener('DOMContentLoaded', function() {
    // Initialize charts based on available data attributes
    initializeCharts();
    
    // Setup event listeners for dashboard filters
    setupFilterListeners();
    
    // Initialize any tooltips
    initializeTooltips();
});

/**
 * Initialize all charts if their canvases exist
 */
function initializeCharts() {
    // Initialize the materiality matrix chart if the canvas exists
    const matrixCanvas = document.getElementById('materialityMatrix');
    if (matrixCanvas && matrixCanvas.hasAttribute('data-matrix-data')) {
        try {
            const matrixData = JSON.parse(matrixCanvas.getAttribute('data-matrix-data'));
            initializeMaterialityMatrix(matrixCanvas, matrixData);
        } catch (e) {
            console.error('Error parsing matrix data:', e);
        }
    }

    // Initialize IRO distribution chart if the canvas exists
    const distributionCanvas = document.getElementById('iroDistributionChart');
    if (distributionCanvas && distributionCanvas.hasAttribute('data-distribution')) {
        try {
            const distributionData = JSON.parse(distributionCanvas.getAttribute('data-distribution'));
            initializeIRODistributionChart(distributionCanvas, distributionData);
        } catch (e) {
            console.error('Error parsing distribution data:', e);
        }
    }

    // Initialize assessment progress chart if the canvas exists
    const progressCanvas = document.getElementById('assessmentProgressChart');
    if (progressCanvas && progressCanvas.hasAttribute('data-progress')) {
        try {
            const progressData = JSON.parse(progressCanvas.getAttribute('data-progress'));
            initializeAssessmentProgressChart(progressCanvas, progressData);
        } catch (e) {
            console.error('Error parsing progress data:', e);
        }
    }
}

/**
 * Initializes the materiality matrix visualization
 * @param {HTMLCanvasElement} canvas - The canvas element for the chart
 * @param {Array} iroData - Array of IRO data objects
 */
function initializeMaterialityMatrix(canvas, iroData) {
    // If no data provided, use empty array
    if (!iroData) iroData = [];
    
    // Create datasets for different IRO types with different colors
    const datasets = [
        {
            label: 'Risks',
            data: iroData.filter(item => item.type === 'Risk').map(item => ({
                x: item.impact_score,
                y: item.financial_score,
                r: 8, // Fixed radius for now
                id: item.id,
                title: item.title
            })),
            backgroundColor: 'rgba(239, 68, 68, 0.7)',
            borderColor: 'rgba(239, 68, 68, 1)'
        },
        {
            label: 'Opportunities',
            data: iroData.filter(item => item.type === 'Opportunity').map(item => ({
                x: item.impact_score,
                y: item.financial_score,
                r: 8, // Fixed radius for now
                id: item.id,
                title: item.title
            })),
            backgroundColor: 'rgba(34, 197, 94, 0.7)',
            borderColor: 'rgba(34, 197, 94, 1)'
        },
        {
            label: 'Impacts',
            data: iroData.filter(item => item.type === 'Impact').map(item => ({
                x: item.impact_score,
                y: item.financial_score,
                r: 8, // Fixed radius for now
                id: item.id,
                title: item.title
            })),
            backgroundColor: 'rgba(59, 130, 246, 0.7)',
            borderColor: 'rgba(59, 130, 246, 1)'
        }
    ];

    // Create the bubble chart
    const matrixChart = new Chart(canvas, {
        type: 'bubble',
        data: {
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Impact Materiality',
                        font: {
                            weight: 'bold'
                        }
                    },
                    min: 0,
                    max: 5,
                    ticks: {
                        stepSize: 1
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Financial Materiality',
                        font: {
                            weight: 'bold'
                        }
                    },
                    min: 0,
                    max: 5,
                    ticks: {
                        stepSize: 1
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const item = context.raw;
                            return [
                                `ID: #${item.id}`,
                                `Title: ${item.title}`,
                                `Impact Materiality: ${item.x.toFixed(1)}`,
                                `Financial Materiality: ${item.y.toFixed(1)}`
                            ];
                        }
                    }
                },
                legend: {
                    position: 'bottom'
                },
                annotation: {
                    annotations: {
                        quadrantLines: {
                            type: 'line',
                            xMin: 2.5,
                            xMax: 2.5,
                            yMin: 0,
                            yMax: 5,
                            borderColor: 'rgba(0, 0, 0, 0.2)',
                            borderWidth: 1,
                            borderDash: [5, 5]
                        },
                        horizontalLine: {
                            type: 'line',
                            xMin: 0,
                            xMax: 5,
                            yMin: 2.5,
                            yMax: 2.5,
                            borderColor: 'rgba(0, 0, 0, 0.2)',
                            borderWidth: 1,
                            borderDash: [5, 5]
                        }
                    }
                }
            }
        }
    });

    // Add click event to navigate to IRO details
    canvas.onclick = function(evt) {
        const points = matrixChart.getElementsAtEventForMode(evt, 'nearest', { intersect: true }, true);
        if (points.length) {
            const firstPoint = points[0];
            const dataset = matrixChart.data.datasets[firstPoint.datasetIndex];
            const iro = dataset.data[firstPoint.index];
            // Navigate to IRO detail page
            window.location.href = `/assessments/iro/${iro.id}/`;
        }
    };
}

/**
 * Initializes the IRO distribution chart
 * @param {HTMLCanvasElement} canvas - The canvas element for the chart
 * @param {Object} distributionData - Object containing distribution data
 */
function initializeIRODistributionChart(canvas, distributionData) {
    // If no data provided, use empty data
    if (!distributionData) {
        distributionData = {labels: [], counts: []};
    }
    
    // Create the pie chart
    const data = {
        labels: distributionData.labels || [],
        datasets: [{
            data: distributionData.counts || [],
            backgroundColor: [
                'rgba(239, 68, 68, 0.7)',
                'rgba(34, 197, 94, 0.7)',
                'rgba(59, 130, 246, 0.7)'
            ],
            borderColor: [
                'rgba(239, 68, 68, 1)',
                'rgba(34, 197, 94, 1)',
                'rgba(59, 130, 246, 1)'
            ],
            borderWidth: 1
        }]
    };

    const distributionChart = new Chart(canvas, {
        type: 'doughnut',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.raw || 0;
                            const total = context.chart.data.datasets[0].data.reduce((a, b) => a + b, 0);
                            const percentage = Math.round((value / total) * 100);
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

/**
 * Initializes the assessment progress chart
 * @param {HTMLCanvasElement} canvas - The canvas element for the chart
 * @param {Object} progressData - Object containing progress data
 */
function initializeAssessmentProgressChart(canvas, progressData) {
    // If no data provided, use empty data
    if (!progressData) {
        progressData = {labels: [], counts: []};
    }
    
    // Create the bar chart
    const data = {
        labels: progressData.labels || [],
        datasets: [{
            label: 'Number of IROs',
            data: progressData.counts || [],
            backgroundColor: [
                'rgba(156, 163, 175, 0.7)',
                'rgba(234, 179, 8, 0.7)',
                'rgba(34, 197, 94, 0.7)',
                'rgba(249, 115, 22, 0.7)'
            ],
            borderColor: [
                'rgba(156, 163, 175, 1)',
                'rgba(234, 179, 8, 1)',
                'rgba(34, 197, 94, 1)',
                'rgba(249, 115, 22, 1)'
            ],
            borderWidth: 1
        }]
    };

    const progressChart = new Chart(canvas, {
        type: 'bar',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Number of IROs',
                        font: {
                            weight: 'bold'
                        }
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}

/**
 * Sets up event listeners for dashboard filters
 */
function setupFilterListeners() {
    // Time period filter for materiality matrix
    const matrixDropdown = document.getElementById('matrixDropdown');
    if (matrixDropdown) {
        const dropdownItems = document.querySelectorAll('[aria-labelledby="matrixDropdown"] .dropdown-item');
        dropdownItems.forEach(item => {
            item.addEventListener('click', function(e) {
                e.preventDefault();
                const selectedPeriod = this.textContent;
                matrixDropdown.textContent = selectedPeriod;
                // Here you would typically fetch new data based on the selected period
                // and update the chart
                updateMatrixData(selectedPeriod);
            });
        });
    }

    // IRO type filter
    const typeFilter = document.getElementById('iroTypeFilter');
    if (typeFilter) {
        typeFilter.addEventListener('change', function() {
            // Filter dashboard data based on selected IRO type
            filterDashboardByType(this.value);
        });
    }

    // Status filter
    const statusFilter = document.getElementById('statusFilter');
    if (statusFilter) {
        statusFilter.addEventListener('change', function() {
            // Filter dashboard data based on selected status
            filterDashboardByStatus(this.value);
        });
    }
}

/**
 * Updates the materiality matrix data based on selected time period
 * @param {string} period - The selected time period
 */
function updateMatrixData(period) {
    // This would typically involve an AJAX call to fetch new data
    console.log(`Updating matrix data for period: ${period}`);
    
    // Example of how you might update the chart with new data
    // In a real implementation, you would fetch this data from your backend
    const matrixCanvas = document.getElementById('materialityMatrix');
    if (matrixCanvas) {
        const chart = Chart.getChart(matrixCanvas);
        if (chart) {
            // Slightly modify the data points to simulate changes
            chart.data.datasets.forEach(dataset => {
                dataset.data.forEach(point => {
                    // Slightly modify the data points to simulate changes
                    point.x += (Math.random() - 0.5) * 0.5;
                    point.y += (Math.random() - 0.5) * 0.5;
                    // Ensure values stay within bounds
                    point.x = Math.max(0, Math.min(5, point.x));
                    point.y = Math.max(0, Math.min(5, point.y));
                });
            });
            chart.update();
        }
    }
}

/**
 * Filters dashboard data based on IRO type
 * @param {string} type - The selected IRO type
 */
function filterDashboardByType(type) {
    console.log(`Filtering dashboard by IRO type: ${type}`);
    
    // This would typically involve updating all relevant dashboard components
    // based on the selected filter
    
    // Example: Update high-priority IROs table
    const iroTable = document.getElementById('highPriorityIROsTable');
    if (iroTable && iroTable.tBodies[0]) {
        const rows = iroTable.tBodies[0].rows;
        for (let i = 0; i < rows.length; i++) {
            const iroType = rows[i].cells[2].querySelector('.badge')?.textContent.trim();
            if (type === 'All' || iroType === type) {
                rows[i].style.display = '';
            } else {
                rows[i].style.display = 'none';
            }
        }
    }
    
    // You would also update other dashboard components like charts
    // based on the selected filter
}

/**
 * Filters dashboard data based on status
 * @param {string} status - The selected status
 */
function filterDashboardByStatus(status) {
    console.log(`Filtering dashboard by status: ${status}`);
    
    // Similar to filterDashboardByType, but filtering based on status
    
    // Example: Update high-priority IROs table
    const iroTable = document.getElementById('highPriorityIROsTable');
    if (iroTable && iroTable.tBodies[0]) {
        const rows = iroTable.tBodies[0].rows;
        for (let i = 0; i < rows.length; i++) {
            const iroStatus = rows[i].cells[5].querySelector('.status-badge')?.textContent.trim();
            if (status === 'All' || iroStatus === status) {
                rows[i].style.display = '';
            } else {
                rows[i].style.display = 'none';
            }
        }
    }
    
    // Example: Update recent activity timeline
    const activityItems = document.querySelectorAll('[data-status]');
    activityItems.forEach(item => {
        const itemStatus = item.getAttribute('data-status');
        if (status === 'All' || itemStatus === status) {
            item.style.display = '';
        } else {
            item.style.display = 'none';
        }
    });
}

/**
 * Initializes Bootstrap tooltips
 */
function initializeTooltips() {
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
}

/**
 * Handles window resize events to ensure charts remain responsive
 */
window.addEventListener('resize', function() {
    const matrixCanvas = document.getElementById('materialityMatrix');
    if (matrixCanvas) {
        const chart = Chart.getChart(matrixCanvas);
        if (chart) {
            chart.resize();
        }
    }
    
    const distributionCanvas = document.getElementById('iroDistributionChart');
    if (distributionCanvas) {
        const chart = Chart.getChart(distributionCanvas);
        if (chart) {
            chart.resize();
        }
    }
    
    const progressCanvas = document.getElementById('assessmentProgressChart');
    if (progressCanvas) {
        const chart = Chart.getChart(progressCanvas);
        if (chart) {
            chart.resize();
        }
    }
});

/**
 * Exports the current materiality matrix as an image
 */
function exportMatrixAsImage() {
    const matrixCanvas = document.getElementById('materialityMatrix');
    if (matrixCanvas) {
        const link = document.createElement('a');
        link.download = 'materiality_matrix.png';
        link.href = matrixCanvas.toDataURL('image/png');
        link.click();
    }
}

/**
 * Initializes search functionality for IRO tables
 */
function initializeSearch() {
    const searchInput = document.getElementById('iroSearch');
    if (searchInput) {
        searchInput.addEventListener('keyup', function() {
            const searchTerm = this.value.toLowerCase();
            const table = document.getElementById('highPriorityIROsTable');
            if (table && table.tBodies[0]) {
                const rows = table.tBodies[0].rows;
                
                for (let i = 0; i < rows.length; i++) {
                    const text = rows[i].textContent.toLowerCase();
                    if (text.indexOf(searchTerm) > -1) {
                        rows[i].style.display = '';
                    } else {
                        rows[i].style.display = 'none';
                    }
                }
            }
        });
    }
}

// Initialize search when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeSearch();
});
</file>

<file path='templates/assessments/assessment_form.html'>
<!-- templates/assessments/assessment_form.html -->
{% extends "base.html" %}

{% block title %}
    Assessment Form
{% endblock %}

{% block content %}
<div class="section">
    <h1>Create / Update Assessment</h1>
    <form method="POST" novalidate>
        {% csrf_token %}
        {{ form.as_p }}

        <button type="submit" class="btn btn-success">Save</button>
        <a href="{% url 'assessments:list' %}" class="btn btn-secondary">Cancel</a>
    </form>
</div>
{% endblock %}
</file>

<file path='templates/assessments/assessment_list.html'>
<!-- templates/assessments/assessment_list.html -->
{% extends "base.html" %}

{% block title %}
    Assessments List
{% endblock %}

{% block content %}
<div class="section">
    <h1>All Assessments</h1>
    <p>
        <a href="{% url 'assessments:create' %}" class="btn btn-primary">Create New Assessment</a>
    </p>

    {% if assessments %}
      <table class="table table-bordered table-striped">
        <thead>
          <tr>
            <th>Name</th>
            <th>Description</th>
            <th>Created On</th>
            <th>Updated On</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
        {% for assessment in assessments %}
          <tr>
            <td>{{ assessment.name }}</td>
            <td>{{ assessment.description|default_if_none:"(No description)" }}</td>
            <td>{{ assessment.created_on|date:"Y-m-d H:i" }}</td>
            <td>{{ assessment.updated_on|date:"Y-m-d H:i" }}</td>
            <td>
              <a href="{% url 'assessments:edit' assessment.pk %}" class="btn btn-sm btn-info">Edit</a>
            </td>
          </tr>
        {% endfor %}
        </tbody>
      </table>
    {% else %}
      <p>No assessments have been created yet.</p>
    {% endif %}
</div>
{% endblock %}
</file>

<file path='templates/assessments/iro_form.html'>
{% extends "base.html" %}
{% load crispy_forms_tags %}

{% block title %}IRO Form | DMA Platform{% endblock %}
{% block page_title %}{% if form.instance.pk %}Edit IRO{% else %}Create New IRO{% endif %}{% endblock %}

{% block content %}
<div class="row">
    <div class="col-lg-10 mx-auto">
        <div class="card shadow-sm mb-4">
            <div class="card-header bg-white py-3">
                <h5 class="card-title mb-0">
                    {% if form.instance.pk %}
                        Edit IRO #{{ form.instance.iro_id }}
                    {% else %}
                        Create New Impact, Risk, or Opportunity
                    {% endif %}
                </h5>
            </div>
            <div class="card-body">
                <form method="POST" novalidate id="iro-form">
                    {% csrf_token %}
                    
                    <div class="row mb-4">
                        <div class="col-md-12">
                            <div class="alert alert-info">
                                <i class="fas fa-info-circle me-2"></i>
                                <span>Complete all required fields to create a new IRO. You can edit additional details after creation.</span>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Basic Information Section -->
                    <div class="row mb-4">
                        <div class="col-12">
                            <h5 class="border-bottom pb-2 mb-3">Basic Information</h5>
                        </div>
                        
                        <div class="col-md-6">
                            {{ form.tenant|as_crispy_field }}
                        </div>
                        
                        <div class="col-md-6">
                            {{ form.type|as_crispy_field }}
                        </div>
                        
                        <div class="col-md-12 mt-3">
                            <div class="form-group">
                                <label for="id_title">Title</label>
                                <input type="text" name="title" class="form-control" id="id_title" placeholder="Enter a clear, descriptive title" required>
                                <div class="form-text text-muted">
                                    Provide a concise title that clearly identifies this IRO
                                </div>
                            </div>
                        </div>
                        
                        <div class="col-md-12 mt-3">
                            <div class="form-group">
                                <label for="id_description">Description</label>
                                <textarea name="description" class="form-control" id="id_description" rows="4" placeholder="Describe this IRO in detail"></textarea>
                                <div class="form-text text-muted">
                                    Include relevant context, scope, and potential implications
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Classification Section -->
                    <div class="row mb-4">
                        <div class="col-12">
                            <h5 class="border-bottom pb-2 mb-3">Classification</h5>
                        </div>
                        
                        <div class="col-md-6">
                            {{ form.source_of_iro|as_crispy_field }}
                        </div>
                        
                        <div class="col-md-6">
                            {{ form.esrs_standard|as_crispy_field }}
                        </div>
                        
                        <div class="col-md-6 mt-3">
                            <div class="form-group">
                                <label for="id_sust_topic_level1">Sustainability Topic (Level 1)</label>
                                <select name="sust_topic_level1" class="form-select" id="id_sust_topic_level1">
                                    <option value="">Select a topic</option>
                                    <option value="climate">Climate</option>
                                    <option value="water">Water & Marine Resources</option>
                                    <option value="biodiversity">Biodiversity & Ecosystems</option>
                                    <option value="pollution">Pollution</option>
                                    <option value="resources">Resources & Circular Economy</option>
                                    <option value="workforce">Workforce</option>
                                    <option value="communities">Communities</option>
                                    <option value="consumers">Consumers & End-users</option>
                                </select>
                            </div>
                        </div>
                        
                        <div class="col-md-6 mt-3">
                            <div class="form-group">
                                <label for="id_value_chain">Value Chain Position</label>
                                <select name="value_chain" class="form-select" id="id_value_chain" multiple>
                                    <option value="upstream">Upstream</option>
                                    <option value="operations">Own Operations</option>
                                    <option value="downstream">Downstream</option>
                                </select>
                                <div class="form-text text-muted">
                                    Hold Ctrl/Cmd to select multiple options
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Status Section -->
                    <div class="row mb-4">
                        <div class="col-12">
                            <h5 class="border-bottom pb-2 mb-3">Status</h5>
                        </div>
                        
                        <div class="col-md-6">
                            {{ form.current_stage|as_crispy_field }}
                        </div>
                        
                        <div class="col-md-6">
                            {{ form.last_assessment_date|as_crispy_field }}
                        </div>
                    </div>
                    
                    <!-- Form Actions -->
                    <div class="row">
                        <div class="col-12 d-flex justify-content-between">
                            <a href="{% url 'assessments:iro-list' %}" class="btn btn-outline-secondary">
                                <i class="fas fa-arrow-left me-1"></i> Cancel
                            </a>
                            <div>
                                <button type="submit" name="save_draft" class="btn btn-outline-primary me-2">
                                    <i class="fas fa-save me-1"></i> Save as Draft
                                </button>
                                <button type="submit" class="btn btn-primary">
                                    <i class="fas fa-check-circle me-1"></i> 
                                    {% if form.instance.pk %}Update{% else %}Create{% endif %} IRO
                                </button>
                            </div>
                        </div>
                    </div>
                </form>
            </div>
        </div>
    </div>
</div>

{% endblock %}

{% block extra_js %}
<script>
    // Form validation enhancement
    document.addEventListener('DOMContentLoaded', function() {
        const form = document.getElementById('iro-form');
        
        form.addEventListener('submit', function(event) {
            let isValid = true;
            const title = document.getElementById('id_title');
            
            if (!title.value.trim()) {
                isValid = false;
                title.classList.add('is-invalid');
                
                if (!title.nextElementSibling || !title.nextElementSibling.classList.contains('invalid-feedback')) {
                    const feedback = document.createElement('div');
                    feedback.classList.add('invalid-feedback');
                    feedback.textContent = 'Title is required';
                    title.parentNode.insertBefore(feedback, title.nextElementSibling);
                }
            } else {
                title.classList.remove('is-invalid');
                title.classList.add('is-valid');
            }
            
            if (!isValid) {
                event.preventDefault();
            }
        });
        
        // Dynamic topic selection
        const topicLevel1 = document.getElementById('id_sust_topic_level1');
        if (topicLevel1) {
            topicLevel1.addEventListener('change', function() {
                // Here you could load subtopics based on the selected level 1 topic
                console.log('Selected topic:', this.value);
                // This would typically trigger an AJAX call or use HTMX to load subtopics
            });
        }
    });
</script>
{% endblock %}

</file>

<file path='templates/assessments/iro_list.html'>
{% extends "base.html" %}

{% load assessment_filters %}


{% block title %}IROs | DMA Platform{% endblock %}
{% block page_title %}IROs{% endblock %}

{% block content %}
    <div class="mb-4">
        <a href="{% url 'assessments:iro-create' %}" class="btn btn-primary">
            <i class="fas fa-plus me-1"></i> Create New IRO
        </a>
    </div>
    
    <div class="card shadow-sm mb-4">
        <div class="card-header bg-white py-3">
            <div class="d-flex justify-content-between align-items-center">
                <h5 class="mb-0">IROs Library</h5>
                <div class="d-flex">
                    <div class="dropdown me-2">
                        <button class="btn btn-outline-secondary dropdown-toggle" type="button" id="typeFilterDropdown" data-bs-toggle="dropdown" aria-expanded="false">
                            Filter by Type
                        </button>
                        <ul class="dropdown-menu" aria-labelledby="typeFilterDropdown">
                            <li><a class="dropdown-item" href="#">All Types</a></li>
                            <li><a class="dropdown-item" href="#">Risk</a></li>
                            <li><a class="dropdown-item" href="#">Opportunity</a></li>
                            <li><a class="dropdown-item" href="#">Impact</a></li>
                        </ul>
                    </div>
                    <div class="dropdown">
                        <button class="btn btn-outline-secondary dropdown-toggle" type="button" id="statusFilterDropdown" data-bs-toggle="dropdown" aria-expanded="false">
                            Filter by Status
                        </button>
                        <ul class="dropdown-menu" aria-labelledby="statusFilterDropdown">
                            <li><a class="dropdown-item" href="#">All Statuses</a></li>
                            <li><a class="dropdown-item" href="#">Draft</a></li>
                            <li><a class="dropdown-item" href="#">In Review</a></li>
                            <li><a class="dropdown-item" href="#">Approved</a></li>
                            <li><a class="dropdown-item" href="#">Disclosed</a></li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="card shadow-sm mb-4">
        <div class="card-body p-0">
            <div class="table-responsive">
                <table class="table table-hover align-middle mb-0">
                    <thead class="bg-light">
                        <tr>
                            <th>IRO ID</th>
                            <th>Title</th>
                            <th>Type</th>
                            <th>ESRS</th>
                            <th>Impact Score</th>
                            <th>Financial Score</th>
                            <th>Status</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for item in iros %}
                        <tr>
                            <td>#{{ item.iro_id }}</td>
                            <td>
                                <div class="d-flex align-items-center">
                                    {% if item.type == 'Risk' %}
                                    <span class="badge bg-danger me-2">R</span>
                                    {% elif item.type == 'Opportunity' %}
                                    <span class="badge bg-success me-2">O</span>
                                    {% else %}
                                    <span class="badge bg-primary me-2">I</span>
                                    {% endif %}
                                    <div>
                                        <div class="fw-medium">{{ item.title }}</div>
                                        <small class="text-muted">{{ item.tenant.tenant_name }}</small>
                                    </div>
                                </div>
                            </td>
                            <td>
                                {% if item.type == 'Risk' %}
                                Risk
                                {% elif item.type == 'Opportunity' %}
                                Opportunity
                                {% else %}
                                Impact
                                {% endif %}
                            </td>
                            <td>{{ item.esrs_standard|default:"--" }}</td>
                            <td>
                                {% if item.last_assessment_score %}
                                <div class="d-flex align-items-center">
                                    <span class="me-2">{{ item.last_assessment_score }}</span>
                                    <div class="progress" style="width: 60px; height: 5px;">
                                        <div class="progress-bar {% if item.last_assessment_score > 3.5 %}bg-danger{% elif item.last_assessment_score > 2.5 %}bg-warning{% else %}bg-success{% endif %}" 
                                            style="width: {{ item.last_assessment_score|floatformat:1|stringformat:'s'|slice:'0:3'|floatformat:1|mul:20 }}%">
                                        </div>
                                    </div>
                                </div>
                                {% else %}
                                --
                                {% endif %}
                            </td>
                            <td>
                                {% if item.last_assessment_score %}
                                <div class="d-flex align-items-center">
                                    <span class="me-2">{{ item.last_assessment_score|add:"-0.2"|floatformat:1 }}</span>
                                    <div class="progress" style="width: 60px; height: 5px;">
                                        <div class="progress-bar {% if item.last_assessment_score > 3.5 %}bg-danger{% elif item.last_assessment_score > 2.5 %}bg-warning{% else %}bg-success{% endif %}" 
                                            style="width: {{ item.last_assessment_score|add:'-0.2'|floatformat:1|stringformat:'s'|slice:'0:3'|floatformat:1|mul:20 }}%">
                                        </div>
                                    </div>
                                </div>
                                {% else %}
                                --
                                {% endif %}
                            </td>
                            <td>
                                {% if item.current_stage == 'Draft' %}
                                Draft
                                {% elif item.current_stage == 'In_Review' %}
                                In Review
                                {% elif item.current_stage == 'Approved' %}
                                Approved
                                {% else %}
                                Disclosed
                                {% endif %}
                            </td>
                            <td>
                                <div class="dropdown">
                                    <button class="btn btn-sm btn-light dropdown-toggle" type="button" data-bs-toggle="dropdown">
                                        Actions
                                    </button>
                                    <ul class="dropdown-menu">
                                        <li>
                                            <a class="dropdown-item" href="{% url 'assessments:iro-edit' item.iro_id %}">
                                                <i class="fas fa-edit me-1"></i> Edit
                                            </a>
                                        </li>
                                        <li>
                                            <a class="dropdown-item" href="#">
                                                <i class="fas fa-clipboard-check me-1"></i> Assess
                                            </a>
                                        </li>
                                        <li>
                                            <a class="dropdown-item" href="#">
                                                <i class="fas fa-eye me-1"></i> View Details
                                            </a>
                                        </li>
                                        <li>
                                            <hr class="dropdown-divider">
                                        </li>
                                        <li>
                                            <a class="dropdown-item text-danger" href="#">
                                                <i class="fas fa-trash-alt me-1"></i> Delete
                                            </a>
                                        </li>
                                    </ul>
                                </div>
                            </td>
                        </tr>
                        {% empty %}
                        <tr>
                            <td colspan="8" class="text-center py-5">
                                <div class="py-5">
                                    <i class="fas fa-clipboard-list fa-3x text-muted mb-3"></i>
                                    <h5>No IROs found</h5>
                                    <p class="text-muted">Create your first IRO to begin the assessment process.</p>
                                    <a href="{% url 'assessments:iro-create' %}" class="btn btn-primary mt-2">
                                        <i class="fas fa-plus me-1"></i> Create New IRO
                                    </a>
                                </div>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    
    <div class="d-flex justify-content-between align-items-center">
        <div>
            <p class="text-muted mb-0">Showing 1-10 of {{ iros|length }} items</p>
        </div>
        <div>
            <nav aria-label="Page navigation">
                <ul class="pagination mb-0">
                    <li class="page-item disabled">
                        <a class="page-link" href="#" tabindex="-1">Previous</a>
                    </li>
                    <li class="page-item active"><a class="page-link" href="#">1</a></li>
                    <li class="page-item"><a class="page-link" href="#">2</a></li>
                    <li class="page-item"><a class="page-link" href="#">3</a></li>
                    <li class="page-item">
                        <a class="page-link" href="#">Next</a>
                    </li>
                </ul>
            </nav>
        </div>
    </div>
{% endblock %}

</file>

<file path='templates/base.html'>
<!-- templates/base.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Double Materiality Assessment Platform{% endblock %}</title>
    <!-- Bootstrap 5 CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- Custom CSS -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary-color: #2563eb;
            --primary-dark: #1e40af;
            --secondary-color: #14b8a6;
            --accent-color: #f97316;
            --success-color: #22c55e;
            --warning-color: #eab308;
            --danger-color: #ef4444;
            --gray-50: #f9fafb;
            --gray-100: #f3f4f6;
            --gray-200: #e5e7eb;
            --gray-300: #d1d5db;
            --gray-600: #4b5563;
            --gray-700: #374151;
            --gray-800: #1f2937;
            --gray-900: #111827;
        }
        
        body {
            font-family: 'Inter', sans-serif;
            background-color: var(--gray-50);
            color: var(--gray-800);
        }
        
        /* Modern card styling */
        .card {
            border-radius: 10px;
            border: none;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 15px rgba(0, 0, 0, 0.1);
        }
        
        /* Modern button styling */
        .btn-primary {
            background-color: var(--primary-color);
            border-color: var(--primary-color);
        }
        
        .btn-primary:hover {
            background-color: var(--primary-dark);
            border-color: var(--primary-dark);
        }
        
        .btn-success {
            background-color: var(--success-color);
            border-color: var(--success-color);
        }
        
        /* Navbar styling */
        .navbar {
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        }
        
        /* Table styling */
        .table {
            border-radius: 8px;
            overflow: hidden;
        }
        
        /* Dashboard metrics */
        .metric-card {
            padding: 1.5rem;
            border-radius: 8px;
            margin-bottom: 1rem;
        }
        
        .metric-value {
            font-size: 2rem;
            font-weight: 700;
        }
        
        .metric-label {
            color: var(--gray-600);
            font-size: 0.9rem;
        }
        
        /* Status badges */
        .status-badge {
            padding: 0.35em 0.65em;
            border-radius: 50rem;
            font-weight: 500;
            font-size: 0.75em;
        }
        
        .status-draft {
            background-color: var(--gray-200);
            color: var(--gray-700);
        }
        
        .status-review {
            background-color: var(--warning-color);
            color: white;
        }
        
        .status-approved {
            background-color: var(--success-color);
            color: white;
        }
        
        .status-disclosed {
            background-color: var(--accent-color);
            color: white;
        }
    </style>
    {% block extra_css %}{% endblock %}
</head>
<body>
    <!-- Modern sidebar navigation -->
    <div class="container-fluid">
        <div class="row">
            <!-- Sidebar -->
            <div class="col-md-3 col-lg-2 d-md-block bg-white sidebar collapse" style="min-height: 100vh; box-shadow: inset -1px 0 0 rgba(0, 0, 0, .1);">
                <div class="position-sticky pt-3">
                    <div class="px-3 py-4 mb-3">
                        <h2 class="h5 mb-0">DMA Platform</h2>
                        <p class="text-muted small">Double Materiality Assessment</p>
                    </div>
                    <ul class="nav flex-column">
                        <li class="nav-item">
                            <a class="nav-link {% if request.path == '/' %}active{% endif %}" href="{% url 'home' %}">
                                <i class="fas fa-home me-2"></i> Dashboard
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link {% if '/iro/' in request.path %}active{% endif %}" href="{% url 'assessments:iro-list' %}">
                                <i class="fas fa-chart-line me-2"></i> IROs
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link {% if '/assessments/' in request.path and not '/iro/' in request.path %}active{% endif %}" href="{% url 'assessments:list' %}">
                                <i class="fas fa-clipboard-check me-2"></i> Assessments
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="#">
                                <i class="fas fa-file-alt me-2"></i> Reports
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="#">
                                <i class="fas fa-users me-2"></i> Stakeholders
                            </a>
                        </li>
                        {% if user.is_staff %}
                        <li class="nav-item mt-3">
                            <span class="sidebar-heading d-flex justify-content-between align-items-center px-3 mt-4 mb-1 text-muted">
                                <span>Administration</span>
                            </span>
                            <a class="nav-link" href="{% url 'admin:index' %}">
                                <i class="fas fa-cog me-2"></i> Admin Panel
                            </a>
                        </li>
                        {% endif %}
                    </ul>
                </div>
            </div>
            
            <!-- Main content -->
            <main class="col-md-9 ms-sm-auto col-lg-10 px-md-4 py-4">
                <!-- templates/base.html - add after the header section -->

                <!-- Header with user info -->
                <div class="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pt-3 pb-2 mb-3 border-bottom">
                    <h1 class="h2">{% block page_title %}Dashboard{% endblock %}</h1>
                    <div class="dropdown">
                        <button class="btn btn-light dropdown-toggle" type="button" id="userDropdown" data-bs-toggle="dropdown" aria-expanded="false">
                            <i class="fas fa-user-circle me-1"></i> User Name
                        </button>
                        <ul class="dropdown-menu dropdown-menu-end" aria-labelledby="userDropdown">
                            <li><a class="dropdown-item" href="#"><i class="fas fa-user me-2"></i> Profile</a></li>
                            <li><a class="dropdown-item" href="#"><i class="fas fa-cog me-2"></i> Settings</a></li>
                            <li><hr class="dropdown-divider"></li>
                            <li><a class="dropdown-item" href="#"><i class="fas fa-sign-out-alt me-2"></i> Logout</a></li>
                        </ul>
                    </div>
                </div>

                <!-- Context Selector -->
                {% include 'components/context_selector.html' %}

                <!-- Content container -->
                <div class="container-fluid">
                    {% block content %}{% endblock %}
                </div>
            </main>
        </div>
    </div>

    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/js/bootstrap.bundle.min.js"></script>
    <!-- Chart.js for data visualization -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <!-- HTMX for dynamic interactions -->
    <script src="https://unpkg.com/htmx.org@1.9.2"></script>
    <!-- Alpine.js for interactive components -->
    <script defer src="https://unpkg.com/alpinejs@3.10.5/dist/cdn.min.js"></script>
    
    {% block extra_js %}{% endblock %}
</body>
</html>

</file>

<file path='templates/components/context_selector.html'>
<!-- templates/components/context_selector.html -->
<div class="context-selector border rounded p-3 mb-4 bg-light">
    <h5 class="mb-3">Current Context</h5>
    
    <div class="row">
        <!-- Tenant Context -->
        <div class="col-md-4">
            <div class="card">
                <div class="card-header">
                    <h6 class="mb-0">Tenant</h6>
                </div>
                <div class="card-body">
                    {% if request.context.tenant %}
                        <p class="mb-1 fw-bold">{{ request.context.tenant.tenant_name }}</p>
                    {% else %}
                        <p class="text-muted mb-1">No tenant selected</p>
                    {% endif %}
                    
                    {% if request.user.is_staff %}
                    <div class="mt-2">
                        <button type="button" class="btn btn-sm btn-outline-primary" 
                                data-bs-toggle="modal" data-bs-target="#tenantSelectorModal">
                            Change
                        </button>
                    </div>
                    {% endif %}
                </div>
            </div>
        </div>
        
        <!-- Assessment Context -->
        <div class="col-md-4">
            <div class="card">
                <div class="card-header">
                    <h6 class="mb-0">Assessment</h6>
                </div>
                <div class="card-body">
                    {% if request.context.assessment %}
                        <p class="mb-1 fw-bold">{{ request.context.assessment.name }}</p>
                        <p class="small text-muted">{{ request.context.assessment.description|truncatechars:50 }}</p>
                    {% else %}
                        <p class="text-muted mb-1">No assessment selected</p>
                    {% endif %}
                    
                    <div class="mt-2">
                        <button type="button" class="btn btn-sm btn-outline-primary"
                                data-bs-toggle="modal" data-bs-target="#assessmentSelectorModal">
                            {% if request.context.assessment %}Change{% else %}Select{% endif %}
                        </button>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- IRO Context -->
        <div class="col-md-4">
            <div class="card">
                <div class="card-header">
                    <h6 class="mb-0">IRO</h6>
                </div>
                <div class="card-body">
                    {% if request.context.iro %}
                        <p class="mb-1 fw-bold">{{ request.context.iro.title }}</p>
                        <div class="badge bg-{% if request.context.iro.type == 'Risk' %}danger{% elif request.context.iro.type == 'Opportunity' %}success{% else %}primary{% endif %}">
                            {{ request.context.iro.type }}
                        </div>
                    {% else %}
                        <p class="text-muted mb-1">No IRO selected</p>
                    {% endif %}
                    
                    <div class="mt-2">
                        <button type="button" class="btn btn-sm btn-outline-primary" 
                                {% if not request.context.assessment %}disabled{% endif %}
                                data-bs-toggle="modal" data-bs-target="#iroSelectorModal">
                            {% if request.context.iro %}Change{% else %}Select{% endif %}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Tenant Selector Modal -->
<div class="modal fade" id="tenantSelectorModal" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Select Tenant</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body">
                <div class="list-group">
                    {% for tenant in available_tenants %}
                    <a href="{% url 'set_context' %}?tenant_id={{ tenant.tenant_id }}&next={{ request.path }}" 
                       class="list-group-item list-group-item-action {% if request.context.tenant == tenant %}active{% endif %}">
                        {{ tenant.tenant_name }}
                    </a>
                    {% empty %}
                    <div class="alert alert-info">No tenants available.</div>
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Assessment Selector Modal -->
<div class="modal fade" id="assessmentSelectorModal" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Select Assessment</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body">
                <div class="list-group">
                    {% for assessment in available_assessments %}
                    <a href="{% url 'set_context' %}?assessment_id={{ assessment.id }}&next={{ request.path }}" 
                       class="list-group-item list-group-item-action {% if request.context.assessment == assessment %}active{% endif %}">
                        <div class="d-flex w-100 justify-content-between">
                            <h6 class="mb-1">{{ assessment.name }}</h6>
                            <small>{{ assessment.created_on|date }}</small>
                        </div>
                        <p class="mb-1 small">{{ assessment.description|truncatechars:100 }}</p>
                    </a>
                    {% empty %}
                    <div class="alert alert-info">No assessments available.</div>
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>
</div>

<!-- IRO Selector Modal -->
<div class="modal fade" id="iroSelectorModal" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Select IRO</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body">
                {% if request.context.assessment %}
                <div class="list-group">
                    {% for iro in available_iros %}
                    <a href="{% url 'set_context' %}?iro_id={{ iro.iro_id }}&next={{ request.path }}" 
                       class="list-group-item list-group-item-action {% if request.context.iro == iro %}active{% endif %}">
                        <div class="d-flex w-100 justify-content-between">
                            <h6 class="mb-1">{{ iro.title }}</h6>
                            <span class="badge bg-{% if iro.type == 'Risk' %}danger{% elif iro.type == 'Opportunity' %}success{% else %}primary{% endif %}">
                                {{ iro.type }}
                            </span>
                        </div>
                        <p class="mb-1 small">{{ iro.description|truncatechars:100 }}</p>
                    </a>
                    {% empty %}
                    <div class="alert alert-info">No IROs available for this assessment.</div>
                    {% endfor %}
                </div>
                {% else %}
                <div class="alert alert-warning">Please select an assessment first.</div>
                {% endif %}
            </div>
        </div>
    </div>
</div>
</file>

<file path='templates/home.html'>
<!-- templates/home.html -->
{% extends "base.html" %}
{% load assessment_filters %}

{% block title %}Dashboard | DMA Platform{% endblock %}
{% block page_title %}Dashboard{% endblock %}

{% block content %}
<div class="row mb-4">
    <!-- Key metrics cards -->
    <div class="col-md-3">
        <div class="card metric-card bg-white">
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <div class="metric-value">{{ total_iros }}</div>
                    <div class="metric-label">Total IROs</div>
                </div>
                <div class="icon-shape rounded-circle bg-primary bg-opacity-10 p-2">
                    <i class="fas fa-chart-line text-primary fs-4"></i>
                </div>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card metric-card bg-white">
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <div class="metric-value">{{ high_materiality_count }}</div>
                    <div class="metric-label">High Materiality</div>
                </div>
                <div class="icon-shape rounded-circle bg-danger bg-opacity-10 p-2">
                    <i class="fas fa-exclamation-triangle text-danger fs-4"></i>
                </div>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card metric-card bg-white">
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <div class="metric-value">{{ pending_reviews_count }}</div>
                    <div class="metric-label">Pending Reviews</div>
                </div>
                <div class="icon-shape rounded-circle bg-warning bg-opacity-10 p-2">
                    <i class="fas fa-hourglass-half text-warning fs-4"></i>
                </div>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card metric-card bg-white">
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <div class="metric-value">{{ completed_assessments_count }}</div>
                    <div class="metric-label">Completed Assessments</div>
                </div>
                <div class="icon-shape rounded-circle bg-success bg-opacity-10 p-2">
                    <i class="fas fa-check-circle text-success fs-4"></i>
                </div>
            </div>
        </div>
    </div>
</div>

<div class="row mb-4">
    <!-- Materiality matrix visualization -->
    <div class="col-md-8">
        <div class="card">
            <div class="card-header bg-white">
                <div class="d-flex justify-content-between align-items-center">
                    <h5 class="mb-0">Materiality Matrix</h5>
                    <div class="dropdown">
                        <button class="btn btn-sm btn-outline-secondary dropdown-toggle" type="button" id="matrixDropdown" data-bs-toggle="dropdown" aria-expanded="false">
                            Last 12 Months
                        </button>
                        <ul class="dropdown-menu" aria-labelledby="matrixDropdown">
                            <li><a class="dropdown-item" href="#">Last 6 Months</a></li>
                            <li><a class="dropdown-item" href="#">Last 3 Months</a></li>
                            <li><a class="dropdown-item" href="#">Custom Range</a></li>
                        </ul>
                    </div>
                </div>
            </div>
            <div class="card-body">
                <canvas id="materialityMatrix" style="height: 300px;" data-matrix-data="{{ materiality_matrix_data }}"></canvas>
            </div>
        </div>
    </div>
    
    <!-- Recent activity timeline -->
    <div class="col-md-4">
        <div class="card">
            <div class="card-header bg-white">
                <h5 class="mb-0">Recent Activity</h5>
            </div>
            <div class="card-body p-0">
                <div class="list-group list-group-flush">
                    {% for activity in recent_activities %}
                    <div class="list-group-item border-0 py-3" data-status="{{ activity.action }}">
                        <div class="d-flex align-items-center">
                            <div class="bg-{{ activity.icon_color }} rounded-circle p-2 me-3">
                                <i class="fas fa-{{ activity.icon }} text-white small"></i>
                            </div>
                            <div>
                                <p class="mb-0 fw-medium">{{ activity.description }}</p>
                                <p class="text-muted small mb-0">{{ activity.timestamp|timesince }} ago</p>
                            </div>
                        </div>
                    </div>
                    {% empty %}
                    <div class="list-group-item border-0 py-3">
                        <p class="text-center text-muted my-3">No recent activity</p>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>
</div>

<div class="row mb-4">
    <!-- Top IROs table -->
    <div class="col-12">
        <div class="card">
            <div class="card-header bg-white">
                <div class="d-flex justify-content-between align-items-center">
                    <h5 class="mb-0">High Priority IROs</h5>
                    <a href="{% url 'assessments:iro-list' %}" class="btn btn-sm btn-outline-primary">View All IROs</a>
                </div>
            </div>
            <div class="card-body p-0">
                <div class="table-responsive">
                    <table class="table table-hover align-middle mb-0" id="highPriorityIROsTable">
                        <thead class="bg-light">
                            <tr>
                                <th>IRO ID</th>
                                <th>Title</th>
                                <th>Type</th>
                                <th>Impact Score</th>
                                <th>Financial Score</th>
                                <th>Status</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for iro in high_priority_iros %}
                            <tr>
                                <td>#{{ iro.iro_id }}</td>
                                <td>{{ iro.title }}</td>
                                <td><span class="badge bg-{% if iro.type == 'Risk' %}danger{% elif iro.type == 'Opportunity' %}success{% else %}primary{% endif %}">{{ iro.type }}</span></td>
                                <td>
                                    <div class="d-flex align-items-center">
                                        <span class="me-2">{{ iro.impact_score|floatformat:1 }}</span>
                                        <div class="progress" style="width: 60px; height: 5px;">
                                            <div class="progress-bar bg-{% if iro.impact_score > 3.5 %}danger{% elif iro.impact_score > 2.5 %}warning{% else %}success{% endif %}" 
                                                style="width: {{ iro.impact_score|floatformat:1|stringformat:'s'|slice:'0:3'|floatformat:1|mul:20 }}%">
                                            </div>
                                        </div>
                                    </div>
                                </td>
                                <td>
                                    <div class="d-flex align-items-center">
                                        <span class="me-2">{{ iro.financial_score|floatformat:1 }}</span>
                                        <div class="progress" style="width: 60px; height: 5px;">
                                            <div class="progress-bar bg-{% if iro.financial_score > 3.5 %}danger{% elif iro.financial_score > 2.5 %}warning{% else %}success{% endif %}" 
                                                style="width: {{ iro.financial_score|floatformat:1|stringformat:'s'|slice:'0:3'|floatformat:1|mul:20 }}%">
                                            </div>
                                        </div>
                                    </div>
                                </td>
                                <td><span class="status-badge status-{{ iro.current_stage|lower }}">{{ iro.current_stage|title }}</span></td>
                                <td>
                                    <div class="dropdown">
                                        <button class="btn btn-sm btn-light dropdown-toggle" type="button" data-bs-toggle="dropdown">
                                            Actions
                                        </button>
                                        <ul class="dropdown-menu">
                                            <li><a class="dropdown-item" href="#">View Details</a></li>
                                            <li><a class="dropdown-item" href="{% url 'assessments:iro-edit' iro.iro_id %}">Edit Assessment</a></li>
                                            <li><a class="dropdown-item" href="#">Add Review</a></li>
                                        </ul>
                                    </div>
                                </td>
                            </tr>
                            {% empty %}
                            <tr>
                                <td colspan="7" class="text-center py-3">No high priority IROs found</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
document.addEventListener('DOMContentLoaded', function () {
    // Initialize materiality matrix using data from database
    const matrixCtx = document.getElementById('materialityMatrix');
    const matrixData = JSON.parse(matrixCtx.getAttribute('data-matrix-data') || '[]');
    
    if (matrixData.length > 0) {
        initializeMatrixChart(matrixCtx, matrixData);
    } else {
        matrixCtx.innerHTML = 'No data available for materiality matrix';
    }
});

function initializeMatrixChart(canvas, data) {
    // Process data into datasets grouped by type
    const riskData = data.filter(item => item.type === 'Risk').map(d => ({
        x: d.impact_score,
        y: d.financial_score,
        id: d.id,
        title: d.title
    }));
    
    const opportunityData = data.filter(item => item.type === 'Opportunity').map(d => ({
        x: d.impact_score,
        y: d.financial_score,
        id: d.id,
        title: d.title
    }));
    
    const impactData = data.filter(item => item.type === 'Impact').map(d => ({
        x: d.impact_score,
        y: d.financial_score,
        id: d.id,
        title: d.title
    }));
    
    const matrixChart = new Chart(canvas.getContext('2d'), {
        type: 'scatter',
        data: {
            datasets: [
                {
                    label: 'Risks',
                    data: riskData,
                    backgroundColor: 'rgba(239, 68, 68, 0.7)',
                    borderColor: 'rgba(239, 68, 68, 1)',
                    borderWidth: 1,
                    pointRadius: 8,
                    pointHoverRadius: 10
                }, 
                {
                    label: 'Opportunities',
                    data: opportunityData,
                    backgroundColor: 'rgba(34, 197, 94, 0.7)',
                    borderColor: 'rgba(34, 197, 94, 1)',
                    borderWidth: 1,
                    pointRadius: 8,
                    pointHoverRadius: 10
                },
                {
                    label: 'Impacts',
                    data: impactData,
                    backgroundColor: 'rgba(59, 130, 246, 0.7)',
                    borderColor: 'rgba(59, 130, 246, 1)',
                    borderWidth: 1,
                    pointRadius: 8,
                    pointHoverRadius: 10
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Impact Materiality'
                    },
                    min: 0,
                    max: 5,
                    grid: {
                        display: true,
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Financial Materiality'
                    },
                    min: 0,
                    max: 5,
                    grid: {
                        display: true,
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const point = context.raw;
                            return `${point.title} (ID: ${point.id})
Impact: ${point.x.toFixed(1)}, Financial: ${point.y.toFixed(1)}`;
                        }
                    }
                }
            }
        }
    });
}
</script>
{% endblock %}
</file>

<file path='tenants/admin.py'>
# tenants/admin.py

from django.contrib import admin
from .models import TenantConfig, TenantDomain

@admin.register(TenantConfig)
class TenantConfigAdmin(admin.ModelAdmin):
    list_display = ('tenant_id', 'tenant_name', 'schema_name', 'created_on')
    search_fields = ('tenant_name', 'schema_name')
    list_filter = ('created_on',)

@admin.register(TenantDomain)
class TenantDomainAdmin(admin.ModelAdmin):
    list_display = ('id', 'domain', 'tenant', 'is_primary')
    list_filter = ('is_primary',)
    search_fields = ('domain',)
</file>

<file path='tenants/api/serializers.py'>
# tenants/api/serializers.py
from rest_framework import serializers
from tenants.models import TenantConfig

class TenantConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = TenantConfig
        fields = ['tenant_id', 'tenant_name', 'schema_name', 'created_on']
</file>

<file path='tenants/api/urls.py'>
# tenants/api/urls.py
from rest_framework.routers import DefaultRouter
from .views import TenantConfigViewSet

router = DefaultRouter()
router.register(r'tenant-configs', TenantConfigViewSet, basename='tenant-config')

urlpatterns = router.urls
</file>

<file path='tenants/api/views.py'>
# tenants/api/views.py
from rest_framework import viewsets, permissions
from tenants.models import TenantConfig
from .serializers import TenantConfigSerializer

class TenantConfigViewSet(viewsets.ModelViewSet):
    queryset = TenantConfig.objects.all()
    serializer_class = TenantConfigSerializer
    permission_classes = [permissions.IsAuthenticated]
</file>

<file path='tenants/apps.py'>
# tenants/apps.py

from django.apps import AppConfig

class TenantsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tenants'
    verbose_name = "Tenants"
</file>

<file path='tenants/management/commands/__init__.py'>

</file>

<file path='tenants/management/commands/init_sample_data.py'>
# tenants/management/commands/init_sample_data.py

from django.core.management.base import BaseCommand
from django.db import transaction, connection
from tenants.models import TenantConfig, TenantDomain
from apps.assessments.models import IRO, ImpactAssessment, RiskOppAssessment
from django_tenants.utils import schema_context

class Command(BaseCommand):
    """
    Creates two tenants (if they do not already exist),
    and for each tenant creates 5 IROs (fully assessed).
    """
    help = 'Prepopulate the database with 2 tenants, each having 5 IROs that are fully assessed.'

    def handle(self, *args, **options):
        # 1) Ensure or create 2 tenants:
        #    - tenant1 with domain tenant1.localhost
        #    - tenant2 with domain tenant2.localhost
        tenant_data = [
            {
                "tenant_name": "tenant1",
                "schema_name": "tenant_tenant1",
                "domain": "tenant1.localhost"
            },
            {
                "tenant_name": "tenant2",
                "schema_name": "tenant_tenant2",
                "domain": "tenant2.localhost"
            }
        ]

        for item in tenant_data:
            tenant = TenantConfig.objects.filter(tenant_name=item["tenant_name"]).first()
            if tenant:
                self.stdout.write(
                    self.style.WARNING(
                        f'Tenant "{item["tenant_name"]}" already exists. Using the existing tenant.'
                    )
                )
            else:
                tenant = TenantConfig(
                    tenant_name=item["tenant_name"],
                    schema_name=item["schema_name"]
                )
                tenant.save()
                # Create a corresponding domain
                TenantDomain.objects.create(
                    domain=item["domain"],
                    tenant=tenant,
                    is_primary=True
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created tenant "{item["tenant_name"]}" with domain "{item["domain"]}".'
                    )
                )
            
            # 2) For each tenant, create 5 IROs fully assessed
            self.create_fully_assessed_iros(tenant)

    @transaction.atomic
    def create_fully_assessed_iros(self, tenant):
        # Log the current schema that Django is using
        current_schema = connection.schema_name
        self.stdout.write(self.style.NOTICE(f"Current schema before IRO creation: {current_schema}"))

        # Important: Switch to the tenant's schema before querying or creating tenant models.
        with schema_context(tenant.schema_name):
            # If the tenant already has 5 or more IROs, skip creation to avoid duplicates.
            existing_count = IRO.objects.filter(tenant=tenant).count()
            self.stdout.write(self.style.NOTICE(
                f"Found {existing_count} existing IROs for tenant {tenant.tenant_name}"
            ))
            
            if existing_count >= 5:
                self.stdout.write(
                    self.style.WARNING(
                        f'Tenant "{tenant.tenant_name}" already has {existing_count} IRO(s). Skipping creation.'
                    )
                )
                return

            # Sample sets of data for demonstration.  
            iro_types = ["Risk", "Opportunity", "Impact", "Risk", "Opportunity"]
            
            for idx in range(5):
                # Check schema again before each IRO creation to ensure it's consistent
                current_schema = connection.schema_name
                self.stdout.write(self.style.NOTICE(
                    f"Current schema before creating IRO #{idx+1}: {current_schema}"
                ))
                
                iro_obj = IRO.objects.create(
                    tenant=tenant,
                    type=iro_types[idx],
                    current_stage='Approved',
                    source_of_iro='Scripted Demo',
                    esrs_standard='ESRS E1',
                    assessment_count=1,
                    last_assessment_score=3.5 + (idx * 0.3),  # Just an example
                )
                
                self.stdout.write(self.style.NOTICE(
                    f"Created IRO with ID: {iro_obj.iro_id} in schema: {current_schema}"
                ))
                
                # Create ImpactAssessment
                impact_assessment = ImpactAssessment.objects.create(
                    iro=iro_obj,
                    tenant=tenant,
                    time_horizon='Short-term',
                    actual_or_potential='Actual',
                    scale_score=4,
                    scope_score=3,
                    irremediability_score=3,
                    likelihood_score=4,
                    severity_score=3.8,
                    impact_materiality_score=3.8,
                    overall_rationale=f'Impact rationale for IRO #{iro_obj.iro_id}',
                )
                
                self.stdout.write(self.style.NOTICE(
                    f"Created ImpactAssessment with ID: {impact_assessment.impact_assessment_id}"
                ))

                # Create RiskOppAssessment
                risk_assessment = RiskOppAssessment.objects.create(
                    iro=iro_obj,
                    tenant=tenant,
                    time_horizon='Short-term',
                    workforce_risk=3,
                    operational_risk=4,
                    reputational_risk=3,
                    likelihood_score=3,
                    financial_magnitude_score=2.5,
                    financial_materiality_score=2.9,
                    overall_rationale=f'Financial rationale for IRO #{iro_obj.iro_id}',
                )
                
                self.stdout.write(self.style.NOTICE(
                    f"Created RiskOppAssessment with ID: {risk_assessment.risk_opp_assessment_id}"
                ))

                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created IRO #{iro_obj.iro_id} and its assessments for tenant: {tenant.tenant_name}'
                    )
                )
        
        # After exiting the `with schema_context(...)` block, Django reverts
        # to the default (public) schema.
        current_schema = connection.schema_name
        self.stdout.write(self.style.NOTICE(
            f"Current schema after all IRO creation: {current_schema}"
        ))
</file>

<file path='tenants/management/commands/init_tenant.py'>
from django.core.management.base import BaseCommand
from tenants.models import TenantConfig, TenantDomain

class Command(BaseCommand):
    help = 'Initialize a new tenant (create if not exists); also ensures a matching domain.'

    def add_arguments(self, parser):
        parser.add_argument('--name', type=str, required=True, help='Name of the tenant (unique).')
        parser.add_argument('--domain', type=str, required=True, help='Domain name to map to this tenant (unique).')

    def handle(self, *args, **options):
        tenant_name = options['name']
        domain_name = options['domain']

        # 1) Check if a tenant with this name already exists
        existing_tenant = TenantConfig.objects.filter(tenant_name=tenant_name).first()
        if existing_tenant:
            self.stdout.write(
                self.style.WARNING(f'Tenant named "{tenant_name}" already exists. Checking associated domain...')
            )
            # 2) Ensure the corresponding domain is also set up
            domain_obj, created = TenantDomain.objects.get_or_create(
                domain=domain_name,
                tenant=existing_tenant,
                defaults={'is_primary': True}
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created domain "{domain_name}" for existing tenant "{tenant_name}".'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'Domain "{domain_name}" also already exists. No changes were made.'
                    )
                )
            return  # Done; no need to create a new tenant

        # 3) If tenant does not exist, create a new one
        tenant = TenantConfig(
            tenant_name=tenant_name,
            schema_name=f'tenant_{tenant_name}'
        )
        tenant.save()

        # 4) Create the domain for the newly created tenant
        domain = TenantDomain(
            domain=domain_name,
            tenant=tenant,
            is_primary=True
        )
        domain.save()

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created tenant "{tenant_name}" with domain "{domain_name}".'
            )
        )
</file>

<file path='tenants/migrations/0001_initial.py'>
# tenants/migrations/0001_initial.py
# Generated by Django 4.2 on YYYY-MM-DD HH:MM

from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='TenantConfig',
            fields=[
                ('tenant_id', models.AutoField(primary_key=True, serialize=False)),
                ('tenant_name', models.CharField(max_length=100, unique=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('schema_name', models.CharField(max_length=63, unique=True)),
            ],
            options={
                'db_table': 'public.tenant_config',
            },
        ),
        migrations.CreateModel(
            name='TenantDomain',
            fields=[
                ('id', models.BigAutoField(auto_created=True,
                                           primary_key=True,
                                           serialize=False,
                                           verbose_name='ID')),
                ('domain', models.CharField(db_index=True,
                                            max_length=253,
                                            unique=True)),
                ('is_primary', models.BooleanField(db_index=True, default=True)),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                             related_name='domains',
                                             to='tenants.tenantconfig')),
            ],
            options={
                'db_table': 'tenant_domain',
            },
        ),
    ]
</file>

<file path='tenants/migrations/__init__.py'>

</file>

<file path='tenants/models.py'>
# tenants/models.py

from django.db import models
from django_tenants.models import TenantMixin, DomainMixin

class TenantConfig(TenantMixin):
    tenant_id = models.AutoField(primary_key=True)
    tenant_name = models.CharField(max_length=100, unique=True)
    created_on = models.DateTimeField(auto_now_add=True)
    schema_name = models.CharField(max_length=63, unique=True)

    auto_create_schema = True
    auto_drop_schema = False

    class Meta:
        db_table = 'public.tenant_config'

    def __str__(self):
        return f"{self.tenant_name} (ID: {self.tenant_id})"

class TenantDomain(DomainMixin):
    tenant = models.ForeignKey(
        TenantConfig,
        related_name='domains',
        on_delete=models.CASCADE
    )

    class Meta:
        db_table = 'tenant_domain'

    def __str__(self):
        return f"Domain: {self.domain} -> Tenant: {self.tenant}"
</file>

<file path='tenants/urls.py'>
# tenants/urls.py
from django.urls import path
from .views import TenantConfigListView, TenantConfigCreateView, TenantConfigUpdateView

app_name = 'tenants'

urlpatterns = [
    path('', TenantConfigListView.as_view(), name='list'),
    path('create/', TenantConfigCreateView.as_view(), name='create'),
    path('<int:pk>/edit/', TenantConfigUpdateView.as_view(), name='edit'),
]
</file>

<file path='tenants/views.py'>
# tenants/views.py
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from .models import TenantConfig

class TenantConfigListView(ListView):
    model = TenantConfig
    template_name = 'tenants/tenant_list.html'
    context_object_name = 'tenants'

class TenantConfigCreateView(CreateView):
    model = TenantConfig
    fields = ['tenant_name', 'schema_name']
    template_name = 'tenants/tenant_form.html'
    success_url = reverse_lazy('tenants:list')

class TenantConfigUpdateView(UpdateView):
    model = TenantConfig
    fields = ['tenant_name', 'schema_name']
    template_name = 'tenants/tenant_form.html'
    success_url = reverse_lazy('tenants:list')
</file>

</Concatenated Source Code>