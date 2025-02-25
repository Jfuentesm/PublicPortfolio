<issue>
(.venv) juanfuentes@MacBookPro IRO_platform % ./run_local.sh
Building Docker images...
[+] Building 20.9s (18/21)                                                         docker:desktop-linux
 => [worker internal] load build definition from Dockerfile                                        0.0s
 => => transferring dockerfile: 708B                                                               0.0s
 => [web internal] load build definition from Dockerfile                                           0.0s
 => => transferring dockerfile: 708B                                                               0.0s
 => [web internal] load metadata for docker.io/library/python:3.11-slim                            0.7s
 => [worker auth] library/python:pull token for registry-1.docker.io                               0.0s
 => [web internal] load .dockerignore                                                              0.0s
 => => transferring context: 2B                                                                    0.0s
 => [worker internal] load .dockerignore                                                           0.0s
 => => transferring context: 2B                                                                    0.0s
 => [worker 1/6] FROM docker.io/library/python:3.11-slim@sha256:42420f737ba91d509fc60d5ed65ed0492  0.1s
 => => resolve docker.io/library/python:3.11-slim@sha256:42420f737ba91d509fc60d5ed65ed0492678a90c  0.1s
 => [web internal] load build context                                                              0.8s
 => => transferring context: 1.43MB                                                                0.7s
 => [worker internal] load build context                                                           0.8s
 => => transferring context: 1.43MB                                                                0.7s
 => CACHED [worker 2/6] RUN apt-get update     && apt-get install -y postgresql-client     && rm   0.0s
 => CACHED [worker 3/6] WORKDIR /app                                                               0.0s
 => CACHED [worker 4/6] COPY requirements.txt /app/                                                0.0s
 => CACHED [web 5/6] RUN pip install --no-cache-dir -r requirements.txt                            0.0s
 => [worker 6/6] COPY . /app/                                                                      7.2s
 => [worker] exporting to image                                                                   11.6s
 => => exporting layers                                                                            5.0s
 => => exporting manifest sha256:d9d5853bacd359de8c2643416e0e1eef5622e9a8303ae151c23c8fb9e25f2c6b  0.0s
 => => exporting config sha256:4ad67272f1c2faf47976b47523b8186712eee47ebc3299316fb19ed2704c9f8b    0.0s
 => => exporting attestation manifest sha256:d1b6bf80230be6eab973d276017c6c4933d0733780b5344c0e88  0.1s
 => => exporting manifest list sha256:349a2729f73ab9098e4db81c1650b8de8fb3fa15db100cd9eb8db5ea0b4  0.0s
 => => naming to docker.io/library/iro_platform-worker:latest                                      0.0s
 => => unpacking to docker.io/library/iro_platform-worker:latest                                   5.6s
 => [web] exporting to image                                                                      11.6s
 => => exporting layers                                                                            5.0s
 => => exporting manifest sha256:d0736a4df898e4d14033297b293252983af5b9a0588166420b793781b8c5d418  0.0s
 => => exporting config sha256:d0d5f2eaab266d7712cdde516720c90d6beac61dbf6bed4fd43de5942480ec62    0.0s
 => => exporting attestation manifest sha256:c6f52d491d01f4ba0c1dc6f6fdc54a402cd9f247099b013db231  0.1s
 => => exporting manifest list sha256:278d2921b342cf96367751b0250f163fb05216a2a501396fb414fb7bd79  0.0s
 => => naming to docker.io/library/iro_platform-web:latest                                         0.0s
 => => unpacking to docker.io/library/iro_platform-web:latest                                      5.6s
 => [worker] resolving provenance for metadata file                                                0.0s
 => [web] resolving provenance for metadata file                                                   0.0s
[+] Building 2/2
 ✔ web     Built                                                                                   0.0s 
 ✔ worker  Built                                                                                   0.0s 
Starting containers in the background...
[+] Running 4/4
 ✔ Container iro_platform-db-1      Healthy                                                       15.9s 
 ✔ Container iro_platform-redis-1   Healthy                                                       15.9s 
 ✔ Container iro_platform-web-1     Started                                                       16.4s 
 ✔ Container iro_platform-worker-1  Started                                                       16.4s 
Ensuring we have migrations for the 'tenants' app...
No changes detected in app 'tenants'
Applying any new migrations...
No changes detected
Applying shared (public) schema migrations...
[standard:public] === Starting migration
[standard:public] Operations to perform:
[standard:public]   Apply all migrations: admin, assessments, auth, contenttypes, guardian, sessions, tenants
[standard:public] Running migrations:
[standard:public]   No migrations to apply.
Initializing or updating the default tenant...
Tenant named "default" already exists. Checking associated domain...
Domain "localhost" also already exists. No changes were made.
Applying tenant-specific migrations...
[1/1 (100%) standard:tenant_default] === Starting migration
[1/1 (100%) standard:tenant_default] Operations to perform:
[1/1 (100%) standard:tenant_default]   Apply all migrations: admin, assessments, auth, contenttypes, guardian, sessions, tenants
[1/1 (100%) standard:tenant_default] Running migrations:
[1/1 (100%) standard:tenant_default]   No migrations to apply.
Tailing logs. Press Ctrl+C to stop.
web-1     | db:5432 - accepting connections
web-1     | No changes detected
web-1     | === Starting migration
web-1     | Operations to perform:
web-1     |   Apply all migrations: admin, assessments, auth, contenttypes, guardian, sessions, tenants
web-1     | Running migrations:
web-1     |   No migrations to apply.
web-1     | === Starting migration
web-1     | Operations to perform:
web-1     |   Apply all migrations: admin, assessments, auth, contenttypes, guardian, sessions, tenants
web-1     | Running migrations:
web-1     |   No migrations to apply.
web-1     | Tenant named "default" already exists. Checking associated domain...
web-1     | Domain "localhost" also already exists. No changes were made.
web-1     | [2025-02-25 02:06:08 +0000] [16] [INFO] Starting gunicorn 20.1.0
web-1     | [2025-02-25 02:06:08 +0000] [16] [INFO] Listening at: http://0.0.0.0:8000 (16)
web-1     | [2025-02-25 02:06:08 +0000] [16] [INFO] Using worker: sync
web-1     | [2025-02-25 02:06:08 +0000] [17] [INFO] Booting worker with pid: 17
redis-1   | 1:C 24 Feb 2025 18:17:33.370 * oO0OoO0OoO0Oo Redis is starting oO0OoO0OoO0Oo
redis-1   | 1:C 24 Feb 2025 18:17:33.370 * Redis version=7.4.2, bits=64, commit=00000000, modified=0, pid=1, just started
redis-1   | 1:C 24 Feb 2025 18:17:33.370 # Warning: no config file specified, using the default config. In order to specify a config file use redis-server /path/to/redis.conf
redis-1   | 1:M 24 Feb 2025 18:17:33.371 * monotonic clock: POSIX clock_gettime
redis-1   | 1:M 24 Feb 2025 18:17:33.373 * Running mode=standalone, port=6379.
redis-1   | 1:M 24 Feb 2025 18:17:33.373 * Server initialized
redis-1   | 1:M 24 Feb 2025 18:17:33.373 * Ready to accept connections tcp
redis-1   | 1:M 24 Feb 2025 19:42:09.074 * 1 changes in 3600 seconds. Saving...
redis-1   | 1:M 24 Feb 2025 19:42:09.092 * Background saving started by pid 960
worker-1  | /usr/local/lib/python3.11/site-packages/celery/platforms.py:840: SecurityWarning: You're running the worker with superuser privileges: this is
worker-1  | absolutely not recommended!
redis-1   | 960:C 24 Feb 2025 19:42:09.109 * DB saved on disk
redis-1   | 960:C 24 Feb 2025 19:42:09.109 * Fork CoW for RDB: current 0 MB, peak 0 MB, average 0 MB
redis-1   | 1:M 24 Feb 2025 19:42:09.196 * Background saving terminated with success
redis-1   | 1:M 24 Feb 2025 20:57:06.481 * 1 changes in 3600 seconds. Saving...
redis-1   | 1:M 24 Feb 2025 20:57:06.498 * Background saving started by pid 1731
redis-1   | 1731:C 24 Feb 2025 20:57:06.520 * DB saved on disk
redis-1   | 1731:C 24 Feb 2025 20:57:06.520 * Fork CoW for RDB: current 0 MB, peak 0 MB, average 0 MB
redis-1   | 1:M 24 Feb 2025 20:57:06.609 * Background saving terminated with success
redis-1   | 1:M 24 Feb 2025 21:57:07.024 * 1 changes in 3600 seconds. Saving...
redis-1   | 1:M 24 Feb 2025 21:57:07.027 * Background saving started by pid 5989
redis-1   | 5989:C 24 Feb 2025 21:57:07.035 * DB saved on disk
redis-1   | 5989:C 24 Feb 2025 21:57:07.036 * Fork CoW for RDB: current 0 MB, peak 0 MB, average 0 MB
redis-1   | 1:M 24 Feb 2025 21:57:07.138 * Background saving terminated with success
redis-1   | 1:M 24 Feb 2025 22:57:08.100 * 1 changes in 3600 seconds. Saving...
redis-1   | 1:M 24 Feb 2025 22:57:08.101 * Background saving started by pid 10264
redis-1   | 10264:C 24 Feb 2025 22:57:08.109 * DB saved on disk
redis-1   | 10264:C 24 Feb 2025 22:57:08.109 * Fork CoW for RDB: current 0 MB, peak 0 MB, average 0 MB
redis-1   | 1:M 24 Feb 2025 22:57:08.206 * Background saving terminated with success
redis-1   | 1:M 24 Feb 2025 23:57:09.016 * 1 changes in 3600 seconds. Saving...
redis-1   | 1:M 24 Feb 2025 23:57:09.019 * Background saving started by pid 14522
redis-1   | 14522:C 24 Feb 2025 23:57:09.026 * DB saved on disk
redis-1   | 14522:C 24 Feb 2025 23:57:09.026 * Fork CoW for RDB: current 0 MB, peak 0 MB, average 0 MB
redis-1   | 1:M 24 Feb 2025 23:57:09.130 * Background saving terminated with success
redis-1   | 1:M 25 Feb 2025 00:57:10.029 * 1 changes in 3600 seconds. Saving...
redis-1   | 1:M 25 Feb 2025 00:57:10.031 * Background saving started by pid 18791
redis-1   | 18791:C 25 Feb 2025 00:57:10.039 * DB saved on disk
redis-1   | 18791:C 25 Feb 2025 00:57:10.040 * Fork CoW for RDB: current 0 MB, peak 0 MB, average 0 MB
redis-1   | 1:M 25 Feb 2025 00:57:10.142 * Background saving terminated with success
redis-1   | 1:M 25 Feb 2025 01:57:11.068 * 1 changes in 3600 seconds. Saving...
redis-1   | 1:M 25 Feb 2025 01:57:11.077 * Background saving started by pid 23004
redis-1   | 23004:C 25 Feb 2025 01:57:11.098 * DB saved on disk
redis-1   | 23004:C 25 Feb 2025 01:57:11.099 * Fork CoW for RDB: current 0 MB, peak 0 MB, average 0 MB
db-1      | 
db-1      | PostgreSQL Database directory appears to contain a database; Skipping initialization
db-1      | 
db-1      | 2025-02-24 18:17:33.476 UTC [1] LOG:  starting PostgreSQL 14.16 (Debian 14.16-1.pgdg120+1) on aarch64-unknown-linux-gnu, compiled by gcc (Debian 12.2.0-14) 12.2.0, 64-bit
db-1      | 2025-02-24 18:17:33.477 UTC [1] LOG:  listening on IPv4 address "0.0.0.0", port 5432
db-1      | 2025-02-24 18:17:33.477 UTC [1] LOG:  listening on IPv6 address "::", port 5432
db-1      | 2025-02-24 18:17:33.481 UTC [1] LOG:  listening on Unix socket "/var/run/postgresql/.s.PGSQL.5432"
db-1      | 2025-02-24 18:17:33.484 UTC [27] LOG:  database system was shut down at 2025-02-24 18:17:20 UTC
db-1      | 2025-02-24 18:17:33.494 UTC [1] LOG:  database system is ready to accept connections
db-1      | 2025-02-24 18:18:57.376 UTC [115] ERROR:  relation "assessment" does not exist at character 134
db-1      | 2025-02-24 18:18:57.376 UTC [115] STATEMENT:  SELECT "assessment"."id", "assessment"."name", "assessment"."description", "assessment"."created_on", "assessment"."updated_on" FROM "assessment" LIMIT 21
db-1      | 2025-02-24 18:18:57.377 UTC [115] ERROR:  relation "assessment" does not exist at character 134
db-1      | 2025-02-24 18:18:57.377 UTC [115] STATEMENT:  SELECT "assessment"."id", "assessment"."name", "assessment"."description", "assessment"."created_on", "assessment"."updated_on" FROM "assessment" LIMIT 21
worker-1  | 
worker-1  | Please specify a different user using the --uid option.
worker-1  | 
worker-1  | User information: uid=0 euid=0 gid=0 egid=0
worker-1  | 
redis-1   | 1:M 25 Feb 2025 01:57:11.185 * Background saving terminated with success
worker-1  |   warnings.warn(SecurityWarning(ROOT_DISCOURAGED.format(
worker-1  |  
worker-1  |  -------------- celery@fd324e250614 v5.2.7 (dawn-chorus)
db-1      | 2025-02-24 18:18:57.379 UTC [115] ERROR:  relation "assessment" does not exist at character 134
worker-1  | --- ***** ----- 
worker-1  | -- ******* ---- Linux-6.12.5-linuxkit-aarch64-with-glibc2.36 2025-02-25 02:06:04
worker-1  | - *** --- * --- 
worker-1  | - ** ---------- [config]
worker-1  | - ** ---------- .> app:         core:0xffff80285d50
worker-1  | - ** ---------- .> transport:   redis://redis:6379/0
worker-1  | - ** ---------- .> results:     disabled://
worker-1  | - *** --- * --- .> concurrency: 8 (prefork)
worker-1  | -- ******* ---- .> task events: OFF (enable -E to monitor tasks in this worker)
worker-1  | --- ***** ----- 
worker-1  |  -------------- [queues]
worker-1  |                 .> celery           exchange=celery(direct) key=celery
worker-1  |                 
db-1      | 2025-02-24 18:18:57.379 UTC [115] STATEMENT:  SELECT "assessment"."id", "assessment"."name", "assessment"."description", "assessment"."created_on", "assessment"."updated_on" FROM "assessment" LIMIT 21
db-1      | 2025-02-24 18:18:57.379 UTC [115] ERROR:  relation "assessment" does not exist at character 134
db-1      | 2025-02-24 18:18:57.379 UTC [115] STATEMENT:  SELECT "assessment"."id", "assessment"."name", "assessment"."description", "assessment"."created_on", "assessment"."updated_on" FROM "assessment" LIMIT 21
db-1      | 2025-02-24 18:18:57.380 UTC [115] ERROR:  relation "assessment" does not exist at character 134
db-1      | 2025-02-24 18:18:57.380 UTC [115] STATEMENT:  SELECT "assessment"."id", "assessment"."name", "assessment"."description", "assessment"."created_on", "assessment"."updated_on" FROM "assessment" LIMIT 21
db-1      | 2025-02-24 18:18:57.381 UTC [115] ERROR:  relation "assessment" does not exist at character 134
worker-1  | 
worker-1  | [tasks]
worker-1  |   . apps.assessments.tasks.example_task
worker-1  | 
worker-1  | [2025-02-25 02:06:05,269: INFO/MainProcess] Connected to redis://redis:6379/0
worker-1  | [2025-02-25 02:06:05,274: INFO/MainProcess] mingle: searching for neighbors
worker-1  | [2025-02-25 02:06:06,295: INFO/MainProcess] mingle: all alone
worker-1  | [2025-02-25 02:06:06,312: WARNING/MainProcess] /usr/local/lib/python3.11/site-packages/celery/fixups/django.py:203: UserWarning: Using settings.DEBUG leads to a memory
worker-1  |             leak, never use this setting in production environments!
worker-1  |   warnings.warn('''Using settings.DEBUG leads to a memory
db-1      | 2025-02-24 18:18:57.381 UTC [115] STATEMENT:  SELECT "assessment"."id", "assessment"."name", "assessment"."description", "assessment"."created_on", "assessment"."updated_on" FROM "assessment" LIMIT 21
worker-1  | 
worker-1  | [2025-02-25 02:06:06,312: INFO/MainProcess] celery@fd324e250614 ready.
db-1      | 2025-02-24 18:18:57.382 UTC [115] ERROR:  relation "assessment" does not exist at character 134
db-1      | 2025-02-24 18:18:57.382 UTC [115] STATEMENT:  SELECT "assessment"."id", "assessment"."name", "assessment"."description", "assessment"."created_on", "assessment"."updated_on" FROM "assessment" LIMIT 21
db-1      | 2025-02-24 18:18:57.382 UTC [115] ERROR:  relation "assessment" does not exist at character 134
db-1      | 2025-02-24 18:18:57.382 UTC [115] STATEMENT:  SELECT "assessment"."id", "assessment"."name", "assessment"."description", "assessment"."created_on", "assessment"."updated_on" FROM "assessment" LIMIT 21
db-1      | 2025-02-24 18:18:57.383 UTC [115] ERROR:  relation "assessment" does not exist at character 134
db-1      | 2025-02-24 18:18:57.383 UTC [115] STATEMENT:  SELECT "assessment"."id", "assessment"."name", "assessment"."description", "assessment"."created_on", "assessment"."updated_on" FROM "assessment" LIMIT 21
db-1      | 2025-02-24 18:18:57.384 UTC [115] ERROR:  relation "assessment" does not exist at character 134
db-1      | 2025-02-24 18:18:57.384 UTC [115] STATEMENT:  SELECT "assessment"."id", "assessment"."name", "assessment"."description", "assessment"."created_on", "assessment"."updated_on" FROM "assessment" LIMIT 21
db-1      | 2025-02-24 18:18:57.385 UTC [115] ERROR:  relation "assessment" does not exist at character 134
db-1      | 2025-02-24 18:18:57.385 UTC [115] STATEMENT:  SELECT "assessment"."id", "assessment"."name", "assessment"."description", "assessment"."created_on", "assessment"."updated_on" FROM "assessment" LIMIT 21

</issue>


<output instruction>
1) Explain if this is already complete, or what is missing 
2) Give me the COMPLETE UPDATED VERSION of each script that needs to be updated or created
</output instruction>



 <Tree of Included Files>
- Dockerfile
- docs/design_document_IROs_fronDjango.md
- Dockerfile
- apps/assessments/__init__.py
- apps/assessments/admin.py
- apps/assessments/api/serializers.py
- apps/assessments/api/urls.py
- apps/assessments/api/views.py
- apps/assessments/apps.py
- apps/assessments/migrations/0001_initial.py
- apps/assessments/migrations/__init__.py
- apps/assessments/models.py
- apps/assessments/tasks.py
- apps/assessments/urls.py
- apps/assessments/views.py
- core/__init__.py
- core/celery.py
- core/settings/__init__.py
- core/settings/base.py
- core/settings/local.py
- core/urls.py
- core/wsgi.py
- docker-compose.yaml
- manage.py
- requirements.txt
- run_local.sh
- scripts/01-init-schemas.sql
- templates/assessments/assessment_form.html
- templates/assessments/assessment_list.html
- templates/base.html
- tenants/admin.py
- tenants/api/serializers.py
- tenants/api/urls.py
- tenants/api/views.py
- tenants/apps.py
- tenants/management/commands/__init__.py
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

WORKDIR /app

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . /app/

# Default command (Docker Compose will typically override this)
CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000"]
</file>

<file path='docs/design_document_IROs_fronDjango.md'>
<solution design document>
# **Purpose-Built Double Materiality Assessment (DMA) SaaS Solution Design Document (AWS Edition)**

## **1. Executive Summary**

This document outlines a **purpose-built Double Materiality Assessment (DMA) SaaS platform**, enabling organizations to track, assess, and report **Impacts, Risks, and Opportunities (IROs)** from both **Impact Materiality** and **Financial Materiality** perspectives per **EU CSRD** and **ESRS** requirements. It integrates the following **refined recommendations** from a respected colleague:

1. **Security Implementation Upgrades**: Holistic audit logging, immutable storage, and strong AWS security services (e.g., WAF, Shield, Cognito, KMS).  
2. **Infrastructure Optimization**: Use **AWS Fargate** initially for container workloads to reduce operational overhead; rely on **Amazon RDS** (PostgreSQL) for primary data storage.  
3. **Revised Feature Phases**: Three-phase approach focusing on security and core features first, advanced capabilities next, and global scale thereafter.  
4. **Cost-Effective Security**: Start with AWS Shield Standard, integrate only necessary security features up front, and scale capabilities based on emerging threats.

The **updated design** ensures improved security posture from day one, reduces complexity in initial deployments, and provides a clear roadmap to scale capabilities and features over time.

---

## **2. System Architecture Overview**

### **2.1 High-Level Architecture**

The solution is organized into four layers:

1. **Presentation Layer**  
   - **User Interface** built using Django (Python) for Double Materiality dashboards and IRO management.  
   - **API Endpoints** for external linkage (ESG data, stakeholder portals).  
   - **Authentication/Authorization** via **Amazon Cognito** (supporting MFA, social logins, and SSO).

2. **Application Layer**  
   - **Core DMA Features**: IRO Inventory, Double Materiality Engine, Workflow Approvals, Audit Trails, ESRS Reporting.  
   - **Enterprise Extensions**: Multi-tenancy, row-level security in RDS, RBAC, integration with **Amazon API Gateway**.  
   - **Serverless Workflow** (optional): AWS Lambda or AWS Step Functions for background tasks (report generation, notifications).

3. **Data Layer**  
   - **Primary Database**: **Amazon RDS (PostgreSQL)** for critical data storage, row-level security, audit logging.  
   - **Optional DynamoDB** (future high-throughput needs): Skipped initially unless specific performance or global distribution use cases arise.  
   - **Immutable Audit Storage**: Use versioned **Amazon S3** buckets for storing logs/audit trails if tamper-evident archives are required.

4. **Infrastructure Layer**  
   - **Container Orchestration**: **AWS Fargate** for containerized Django services (option to migrate to full EKS if operational scale warrants it).  
   - **Network & Security**: AWS WAF, Security Groups, AWS Shield (Standard to start, upgrade if needed), Amazon GuardDuty, Cognito, KMS.  
   - **Monitoring & Observability**: Amazon CloudWatch, AWS X-Ray for distributed tracing, AWS Security Hub, and AWS Backup.

**High-Level Architecture Diagram** (using Mermaid):

```mermaid
flowchart TB
    classDef presentation fill:#81D4FA,stroke:#0288D1,color:#000,stroke-width:1px
    classDef application fill:#C5E1A5,stroke:#558B2F,color:#000,stroke-width:1px
    classDef data fill:#FBE9E7,stroke:#BF360C,color:#000,stroke-width:1px,shape:cylinder
    classDef infra fill:#F8BBD0,stroke:#AD1457,color:#000,stroke-width:1px

    User(Stakeholders / Sustainability Teams)
    User --> SB[Security Boundary]

    subgraph SB[Security Boundary]
      direction TB

      subgraph PL[Presentation Layer]
      UI["Django-based Web UI"]:::presentation
      API([API Endpoints]):::presentation
      Auth([Amazon Cognito]):::presentation
      end

      subgraph AL[Application Layer]
      IROs((IRO Inventory)):::application
      DME((Double Materiality Engine)):::application
      Workflow((Review & Approval Workflow)):::application
      Signoff((Sign-off & Validation)):::application
      Audit((Audit Trails)):::application
      ESRS((CSRD/ESRS Reporting)):::application

      MultiT(((Multi-Tenancy & RBAC))):::application
      APIGateway(((Amazon API Gateway))):::application
      end

      subgraph DL[Data Layer]
      RDS["Amazon RDS (PostgreSQL)"]:::data
      S3Data["Versioned S3 Buckets (Audit)"]:::data
      end

      subgraph IL[Infrastructure Layer]
      Fargate{{AWS Fargate}}:::infra
      Monitor{{CloudWatch & X-Ray}}:::infra
      Security{{AWS WAF / Shield / GuardDuty}}:::infra
      Secrets{{AWS KMS / Secrets Manager}}:::infra
      end
    end

    PL --> AL
    AL --> DL
    AL --> IL
    DL --> IL

    Auth --> AL
    AL --> Monitor
    AL --> Security
    AL --> Secrets
    Fargate --> AL
    RDS --> Monitor
    S3Data --> Monitor
```

---

### **2.2 Technology Stack Details**

- **Application Framework**: **Django (Python)** for rapid development, robust security defaults, and admin UI.  
- **Container Deployment**: **AWS Fargate** tasks or services to reduce the operational overhead of managing Kubernetes.  
  - *Future Option*: Migrate to **Amazon EKS** if advanced orchestration, custom scheduling, or large-scale microservices demands arise.  
- **Database**: **Amazon RDS (PostgreSQL)** with row-level security for multi-tenancy, encryption at rest, and simplified audit trails.  
  - **Potential DynamoDB** usage if extremely high-scale or globally distributed data ingestion is needed later.  
- **Security Services**: AWS WAF, Security Groups, AWS Shield (Standard initially, upgrade if needed), Amazon Cognito, AWS KMS.  
- **Observability**: Amazon CloudWatch (metrics, logs), AWS X-Ray (tracing), and AWS Security Hub to unify security findings.

---

## **3. Core Functionality Design**

### **3.1 Detailed Component Breakdown**

1. **IRO Inventory Management**  
   - Captures **Impacts, Risks, and Opportunities** with properties such as category, financial exposure, likelihood, severity, etc.  
   - Import excel-based IRO libraries and supporting documentation with manual CSV import templates (performed by user) or scheduled batch imports. Introduce partial or full real-time integrations in Phase 2 or 3 of the rollout—particularly for high-value use cases that demand live ESG data.
   - Ensures multi-tenant isolation via dedicated schemas in a single PostgreSQL.

2. **Double Materiality Assessment Engine**  
   - **Impact Materiality**: Evaluates external impact magnitude, scope, and likelihood.  
   - **Financial Materiality**: Assesses financial severity and probability of risks/opportunities.  
   - Combines both to identify the most critical IROs for compliance and strategic decisions.

3. **Review & Approval Workflow**  
   - Configurable stage-based review: *Draft → In_Review → Approved → Disclosed*.  
   - Incorporates role-based escalations and notifications via Amazon EventBridge or AWS Lambda triggers.  
   - Flexible time-bound reviews to meet compliance deadlines.

4. **Sign-off & Validation**  
   - Electronic sign-off with a tamper-proof audit trail.  
   - Supports third-party eSignature services if required (DocuSign, Adobe Sign).  
   - Sign-off records stored in **versioned S3** or **immutable** data structures if long-term immutability is needed.

5. **Audit Trails & Logging**  
   - Comprehensive logging (create, update, delete actions) across all modules.  
   - Uses CloudWatch Logs + AWS X-Ray for advanced correlation; optionally store logs in **S3** with versioning for immutability.  
   - Facilitates SOC 2, GDPR, and general compliance requirements from day one.

6. **CSRD/ESRS Reporting**  
   - Generates standardized reports for Impact Materiality, Financial Materiality, and overall alignment with ESRS.  
   - Publish to PDF, CSV, or Excel; push to external systems via **Amazon API Gateway** or S3 pre-signed URLs.

7. **Multi-Tenancy & RBAC**  
   - **Row-level security** enforced at the database layer for strict tenant data isolation.  
   - Role-based access controls to limit unauthorized user actions.  
   - Extendable to more granular permission sets if needed.

8. **API Integrations & Gateways**  
   - **Amazon API Gateway**: Rate limiting, request transformation, and easy versioning.  
   - **Webhook Support**: Outbound webhooks for real-time updates or integrated reporting workflows.  
   - Employ Edge-optimized endpoints if global low-latency access is needed.

---

### **3.2 Data Models and Relationships**

Below is a high-level representation of the primary entities:

```
 IRO                1--n       DMAssessment
 ┌─────────────┐                ┌────────────────────────┐
 │iro_id (PK)   │                │assessment_id (PK)      │
 │tenant_id     │<--------------│iro_id (FK -> IRO)      │
 │type          │               │impact_materiality_json │
 │title         │               │financial_materiality_json
 │description   │               │aggregated_score        │
 │...           │               │assessed_on             │
 └─────────────┘               └────────────────────────┘

 Review             1--n        Signoff
 ┌─────────────┐                ┌─────────────────────┐
 │review_id (PK)│                │signoff_id (PK)      │
 │iro_id (FK)   │<--------------│review_id (FK ->Review)
 │reviewer_id   │               │signed_by            │
 │status        │               │signed_on            │
 │...           │               │signature_ref        │
 └─────────────┘               └─────────────────────┘

         AuditTrail
         ┌─────────────────────────────┐
         │audit_id (PK)               │
         │tenant_id                   │
         │entity_type                 │
         │entity_id                   │
         │action                      │
         │timestamp                   │
         │data_diff (JSON)            │
         └─────────────────────────────┘
```

- **Tenant-Aware**: Each record includes a `tenant_id` for multi-tenant partitioning.  
- **Row-Level Security**: PostgreSQL policies can restrict row access based on `tenant_id`.  
- **Auditing**: Logs every action for compliance, with optional storage in immutable S3.

---

### **3.3 API Design and Endpoints**

- **`POST /api/v1/iros/`**: Create a new IRO.  
- **`GET /api/v1/iros/`**: Retrieve a list of IROs (supports filtering, pagination).  
- **`GET /api/v1/iros/{iro_id}/`**: Get details of a specific IRO.  
- **`POST /api/v1/iros/{iro_id}/assessments/`**: Create a Double Materiality Assessment.  
- **`GET /api/v1/reviews/{review_id}/`**: Retrieve a specific review’s status.  
- **`POST /api/v1/reviews/{review_id}/signoff/`**: Perform sign-off.  
- **`GET /api/v1/audittrails/`**: Query system audit logs.  
- **`GET /api/v1/csrd-reports/`**: Generate or retrieve a pre-built CSRD/ESRS report.

**Authentication & Authorization**  
- All endpoints require **Amazon Cognito** JWT tokens (Bearer).  
- RBAC enforced in Django and row-level security in RDS.  

**Rate Limiting & Versioning**  
- **Amazon API Gateway** handles rate limits and usage plans (e.g., 100 requests/min per user).  
- **Versioning** strategy: URL-based versioning (`/api/v1` → `.../v2`).

---

## **4. Enterprise Architecture Considerations**

### **4.1 Scalability and Performance**

1. **Compute Scalability**  
   - **AWS Fargate** tasks autoscale based on CPU or memory thresholds.  
   - Evaluate migrating to **Amazon EKS** if more control over container orchestration is needed (e.g., sidecar proxies, node-level customizations).

2. **Database Scaling**  
   - **Amazon RDS (PostgreSQL)** can be vertically scaled or use read replicas.  
   - Implement partitioning if extremely large data sets become the norm.

3. **Caching**  
   - **Amazon ElastiCache (Redis)** for frequently accessed data (e.g., aggregated DMA results, reference data).  
   - Improves performance under heavy read loads.

4. **CDN/Global Deployment**  
   - **Amazon CloudFront** or **AWS Global Accelerator** for global content delivery, especially for distributed tenant bases.  
   - Multi-region architecture in Phase 3 if agility and data residency demands arise.

5. **Performance Monitoring**  
   - **Amazon CloudWatch** (metrics, logs), AWS X-Ray (tracing).  
   - Review logs in real time to proactively address latency or resource bottlenecks.

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

class IROViewSet(viewsets.ModelViewSet):
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

########################
# Existing CBVs for Assessment
########################

class AssessmentListView(ListView):
    model = Assessment
    template_name = 'assessments/assessment_list.html'
    context_object_name = 'assessments'


class AssessmentCreateView(CreateView):
    model = Assessment
    fields = ['name', 'description']
    template_name = 'assessments/assessment_form.html'
    success_url = reverse_lazy('assessments:list')


class AssessmentUpdateView(UpdateView):
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

class IROListView(ListView):
    model = IRO
    template_name = 'assessments/iro_list.html'
    context_object_name = 'iros'


class IROCreateView(CreateView):
    model = IRO
    form_class = IROForm
    template_name = 'assessments/iro_form.html'
    success_url = reverse_lazy('assessments:iro-list')


class IROUpdateView(UpdateView):
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

MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    # The tenant middleware must appear near the top (before DB queries occur):
    'django_tenants.middleware.main.TenantMainMiddleware',

    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
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

<file path='core/urls.py'>
# core/urls.py
from django.contrib import admin
from django.http import HttpResponse
from django.urls import path, include

def home(request):
    return HttpResponse("Welcome to the IRO Platform!")

urlpatterns = [
    path('', home, name='home'),
    path('admin/', admin.site.urls),
    path('assessments/', include('apps.assessments.urls')),  # Existing
    path('tenants/', include('tenants.urls', namespace='tenants')),  # Existing

    # NEW: Register the DRF endpoints
    path('api/assessments/', include('apps.assessments.api.urls')),  
    path('api/tenants/', include('tenants.api.urls')), 
]
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
        # Create any needed migrations (including for the 'tenants' app).
        python manage.py makemigrations;
        # Apply shared (public) schema migrations first, creating public.tenant_config
        python manage.py migrate_schemas --shared;
        # Apply tenant-specific migrations in each tenant schema
        python manage.py migrate_schemas --tenant;
        # Only now can we safely initialize or update the 'default' tenant
        python manage.py init_tenant --name=default --domain=localhost;
        # Finally, start Gunicorn
        gunicorn core.wsgi:application --bind 0.0.0.0:8000
      "
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
docker compose build

echo "Starting containers in the background..."
docker compose up -d

echo "Ensuring we have migrations for the 'tenants' app..."
docker compose exec web python manage.py makemigrations tenants

echo "Applying any new migrations..."
docker compose exec web python manage.py makemigrations

echo "Applying shared (public) schema migrations..."
docker compose exec web python manage.py migrate_schemas --shared

echo "Initializing or updating the default tenant..."
docker compose exec web python manage.py init_tenant --name=default --domain=localhost

echo "Applying tenant-specific migrations..."
docker compose exec web python manage.py migrate_schemas --tenant

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

<file path='templates/base.html'>
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{% block title %}Default Title{% endblock %}</title>
  <!-- Include your CSS here -->
</head>
<body>
  <header>
    <h2>Site Header</h2>
  </header>

  <main>
    {% block content %}
    <!-- Child templates override this content block -->
    {% endblock %}
  </main>

  <footer>
    <p>&copy; 2025 MyProject</p>
  </footer>
</body>
</html>
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