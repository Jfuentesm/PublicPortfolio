<goal>
### **LDE-4: Implement Gunicorn & Celery in Containers**

- **ID**: LDE-4  
- **Title**: *Production-like Service Commands*  
- **Description**: Update the Docker Compose service definitions to run Gunicorn for the Django web container and Celery worker for async tasks. Mirror the commands used for AWS deployment to ensure parity (e.g., Gunicorn command, Celery worker arguments).  
- **Acceptance Criteria**:  
  1. Web container runs Gunicorn with accessible logs.  
  2. Celery worker container logs show normal queue listening.  
  3. Logging format matches or approximates production usage (JSON logs, or structured logs if required).  
  4. Both services remain stable under basic load testing.  
- **Technical Dependencies**:  
  - Dockerfile references to `gunicorn` and `celery` installed via `requirements.txt`  
  - Properly configured environment variables (`CELERY_BROKER_URL`, `DATABASE_URL`)  </goal>


<output instruction>
1) Explain if already satisfied. If not, what is missing?
2) Give me the COMPLETE UPDATED VERSION of each script that needs to be updated
</output instruction>



 <Tree of Included Files>
- compose.yaml
- Dockerfile
- docs/design_document_IROs_AWSv2withQ&AwithArchdesignanduserfront.md
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

<file path='docs/design_document_IROs_AWSv2withQ&AwithArchdesignanduserfront.md'>
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

---

### **4.2 Security Architecture**

1. **Security Implementation (Refined)**  
   - **Comprehensive Audit Trails**: Log all system events and changes to an immutable store (versioned S3).  
   - **WAF, Shield, Security Groups**: Protect application endpoints from common threats and DDoS.  
   - **Data Encryption**: KMS for RDS, server-side encryption for S3.  
   - **Row-Level Security**: Strict multi-tenant data isolation at the database layer.  
   - **Cognito Authentication**: Enforce MFA and single sign-on integration.

2. **Compliance & Governance**  
   - Align with **SOC 2**, **GDPR**, and emerging **CSRD/ESRS** guidelines.  
   - Periodic penetration testing and vulnerability scans.  
   - Use **AWS Security Hub** + **GuardDuty** to centralize security alerts.

3. **Identity & Access Management**  
   - **Least Privilege**: Limit IAM roles and security group scope.  
   - Integrate AWS Organizations for environment-wide service control policies.  
   - Maintain read-only audit logs for forensic review if needed.

4. **Cost-Effective Security**  
   - Use **AWS Shield Standard** initially (upgrade to Advanced as threats escalate).  
   - Implement the essential logging and threat detection; add advanced tooling only when justified by risk profile.  
   - Leverage built-in RDS/PostgreSQL security before expanding with specialized third-party tools.

---

### **4.3 Azure Infrastructure Design (Adapted for AWS)**

*(Note: The original heading mentions Azure. Below is the AWS-equivalent design to maintain consistency with the rest of the document.)*

1. **AWS Fargate Deployment**  
   - Simple container context: Fargate tasks for Django web services.  
   - Automatic patching and minimal management overhead.

2. **Amazon RDS (PostgreSQL)**  
   - Multi-AZ configuration for high availability.  
   - Point-in-time recovery, backups configured with AWS Backup.  
   - Row-level security for multi-tenant separation.

3. **Networking & Security**  
   - Private subnets for application tasks and database.  
   - Public subnets only for load balancers / API Gateway endpoints.  
   - VPC flow logs for tracing inbound/outbound traffic.

4. **Monitoring & Logging**  
   - **Amazon CloudWatch** for container metrics, AWS X-Ray for application tracing.  
   - **AWS Security Hub** + **GuardDuty** for threat detection and compliance checks.

---

## **5. Implementation Recommendations**

### **5.1 Development Phases (Refined)**

**Phase 1: Essential Security + Core Features**  
- **Multi-tenant data isolation** using row-level security in RDS.  
- **Basic IRO management** (Impacts, Risks, Opportunities).  
- **Fundamental Double Materiality** calculations for Impact & Financial aspects.  
- **Core Security Controls**: WAF, Shield Standard, Security Groups, KMS encryption.  
- **Advanced Workflows**: Review & Approval pipelines.  
- **Detailed Audit Trails**: CloudWatch logs, versioned S3 for immutable storage.

**Phase 2: Enhanced Capabilities**  
- **AI/ML Analytics**: Integrate advanced analytics (e.g., Amazon SageMaker) for risk forecasting or materiality scoring.  
- **Extended Integrations**: Connect external ESG data, third-party sign-off platforms, or ERPs.  
- **API Maturity**: Expand versioning, webhook subscriptions, refined rate limits in API Gateway.

**Phase 3: Scale + Future Features**  
- **Multi-Region Support**: Active-passive or active-active architecture for global coverage.  
- **Disaster Recovery**: Cross-region replication for RDS, region failover strategies.  
- **Additional Features**: Based on market demand (e.g., real-time IoT data ingestion, partner marketplaces).

---

### **5.2 Best Practices**

- **Infrastructure as Code**: Use CloudFormation, AWS CDK, or Terraform to provision environments reliably.  
- **DevSecOps**: Integrate scanning tools (SAST/DAST) in pipelines, adopt automatic container image checks.  
- **Zero Trust**: Enforce least privilege, strong identity controls, and isolate workloads in separate VPC subnets.  
- **Regular DR Drills**: Validate RPO (Recovery Point Objective) / RTO (Recovery Time Objective) with simulated failovers.  
- **Cost Optimization**: Monitor usage in AWS Cost Explorer, adopt instance savings plans or Fargate savings if usage patterns are predictable.

---

## **6. Appendices**

### **6.1 Database Schema (Example)**

```sql
CREATE TABLE dbo.IRO (
    iro_id SERIAL PRIMARY KEY,
    tenant_id INT NOT NULL,
    type VARCHAR(20) NOT NULL, -- Impact, Risk, Opportunity
    title VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    owner_id INT NOT NULL,
    created_on TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE dbo.DMAssessment (
    assessment_id SERIAL PRIMARY KEY,
    iro_id INT NOT NULL REFERENCES dbo.IRO(iro_id),
    impact_materiality_json TEXT,
    financial_materiality_json TEXT,
    aggregated_score NUMERIC(5,2),
    assessed_on TIMESTAMP NOT NULL DEFAULT NOW(),
    assessed_by INT NOT NULL
);

CREATE TABLE dbo.Review (
    review_id SERIAL PRIMARY KEY,
    iro_id INT NOT NULL REFERENCES dbo.IRO(iro_id),
    reviewer_id INT NOT NULL,
    status VARCHAR(50) NOT NULL,
    created_on TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE dbo.Signoff (
    signoff_id SERIAL PRIMARY KEY,
    review_id INT NOT NULL REFERENCES dbo.Review(review_id),
    signed_by INT NOT NULL,
    signed_on TIMESTAMP NOT NULL DEFAULT NOW(),
    signature_ref VARCHAR(255)
);

CREATE TABLE dbo.AuditTrail (
    audit_id SERIAL PRIMARY KEY,
    entity_type VARCHAR(50),
    entity_id INT,
    action VARCHAR(50),
    user_id INT,
    tenant_id INT,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    data_diff TEXT
);
```

- **Tenant Field**: `tenant_id` is crucial for row-level security.  
- **RLS Policies**: One policy per table can restrict `tenant_id` to the user’s assigned tenant.  
- **Backups**: Enabled automatically in RDS; use AWS Backup and store long-term in S3.

---

### **6.2 API Documentation (Sample)**

| Endpoint                                          | Method | Description                                                          | Auth Required | Rate Limit/min |
|---------------------------------------------------|--------|----------------------------------------------------------------------|--------------|---------------|
| `/api/v1/iros/`                                   | POST   | Create a new IRO                                                     | Yes          | 50            |
| `/api/v1/iros/`                                   | GET    | List/filter existing IROs                                           | Yes          | 100           |
| `/api/v1/iros/{iro_id}/`                          | GET    | Retrieve a single IRO                                               | Yes          | 100           |
| `/api/v1/iros/{iro_id}/`                          | PUT    | Update a specific IRO                                               | Yes          | 50            |
| `/api/v1/iros/{iro_id}/assessments/`              | POST   | Submit a Double Materiality Assessment                              | Yes          | 50            |
| `/api/v1/reviews/`                                | GET    | List reviews (filter by status, date)                               | Yes          | 100           |
| `/api/v1/reviews/{review_id}/signoff/`            | POST   | Provide digital sign-off for a review                               | Yes          | 25            |
| `/api/v1/audittrails/`                            | GET    | Query system audit logs                                             | Yes          | 100           |
| `/api/v1/csrd-reports/`                           | GET    | Generate/fetch CSRD/ESRS compliance reports                         | Yes          | 25            |

- **Versioning**: Additional endpoints or changes introduced at `/api/v2/...`.  
- **Webhooks**: Subscribe to changes in IRO or assessment statuses, configured via custom endpoints.

---

### **6.3 Infrastructure Diagrams (AWS Fargate Emphasis)**

```mermaid
flowchart LR
    classDef infra fill:#F8BBD0,stroke:#AD1457,color:#000,stroke-width:1px

    CF(CloudFront / Route53):::infra
    WAF{{AWS WAF + Shield}}:::infra
    APIG((Amazon API Gateway)):::infra
    Fargate((AWS Fargate)):::infra
    RDS[(Amazon RDS)]:::infra
    SM{{AWS Secrets Manager}}:::infra
    S3[(Amazon S3 - versioned)]:::infra
    Cognito((Amazon Cognito)):::infra
    CW{{Amazon CloudWatch + X-Ray}}:::infra

    CF --> WAF
    WAF --> APIG
    APIG --> Fargate
    Fargate --> RDS
    Fargate --> SM
    Fargate --> S3
    Cognito --> APIG
    Cognito --> Fargate
    Fargate --> CW
    RDS --> CW
```

- **AWS Fargate**: Runs containers with minimal operational overhead.  
- **Amazon RDS**: Managed PostgreSQL for the core data store.  
- **S3 (Versioned)**: Storing immutable logs/audit evidence.  
- **CloudWatch/X-Ray**: Central logging, tracing, and metric analysis.

---

## **Conclusion**

By adopting **AWS Fargate** for containers, focusing on **Amazon RDS** for data isolation, and embedding **day-one security** through comprehensive auditing, encryption, and threat detection, this updated design balances ease of implementation with the flexibility to grow. **Phased feature** rollouts ensure critical security and multi-tenant needs are met first, followed by advanced analytics and global scale in later phases. Future enhancements—like migrating to **Amazon EKS** for more granular container orchestration or incorporating **DynamoDB** for specific high-volume use cases—are still possible. Ultimately, this approach provides a **cost-effective, secure, and compliant** foundation for a Double Materiality Assessment SaaS platform, ready to satisfy **EU CSRD**, **ESRS**, and broader enterprise requirements. 
</solution design document>


<consolidated Q&A bank>
Below is a **consolidated Q&A bank** divided into the four requested sections—**Assessment Framework**, **Data Architecture**, **User Interface**, and **Compliance**—with each question **numbered sequentially**. For each question, you will find:

- The **Question** text.  
- A **Recommended Solution** (summarizing the optimal approach).  
- A brief **Justification** explaining why that solution is advisable.

---

## **1. Assessment Framework**

---

### **Question 1**  
**How should the Double Materiality Assessment scoring be structured or implemented to handle organization-specific rubrics while maintaining consistent core criteria?**  

**Recommended Solution:**  
Provide a **baseline rubric** that covers both Impact Materiality (severity, scale, scope, irreversibility, likelihood) and Financial Materiality (magnitude, likelihood). Allow each organization to **customize numeric scales** (e.g., 1–5) and define how to interpret each level, then store **versioned rubrics** so changes are tracked over time.

**Justification:**  
- **Compliance**: Ensures all essential CSRD/ESRS criteria are met (impact and financial perspectives).  
- **Flexibility**: Accommodates different industries, business units, or internal scoring preferences.  
- **Auditability**: Version control creates a clear trail of scoring changes for regulators or internal auditors.

---

### **Question 2**  
**How frequently should organizations update their Double Materiality Assessments to remain compliant with EU CSRD?**  

**Recommended Solution:**  
Perform a **comprehensive annual** review of all IROs to align with the annual reporting cycle. Additionally, conduct **quarterly or biannual spot checks** for high-priority or rapidly evolving issues, ensuring critical changes are captured promptly.

**Justification:**  
- **Regulatory Alignment**: An annual formal update aligns with standard CSRD disclosure timelines.  
- **Risk Management**: More frequent interim checks on critical areas prevent material blind spots.  
- **Operational Practicality**: Balances compliance needs with organizational bandwidth.

---

### **Question 3**  
**Which approach should be used to identify and categorize IROs (Impacts, Risks, and Opportunities) across various business units and supply chains?**  

**Recommended Solution:**  
Use a **hybrid taxonomy** anchored to recognized sustainability standards (like ESRS categories) while supporting **custom sub-categories** for specific industries or sites. Incorporate **stakeholder input** (employees, suppliers, communities) to ensure all relevant IROs are captured.

**Justification:**  
- **Standardization**: Anchoring to common frameworks simplifies reporting and benchmarking.  
- **Customization**: Industry- or site-specific tags allow deeper granularity where needed.  
- **Holistic Coverage**: Engaging multiple stakeholder groups helps uncover hidden or emerging IROs.

---

### **Question 4**  
**How should scenario analysis be integrated into the Double Materiality Assessment to account for future climate or regulatory changes?**

**Recommended Solution:**  
Provide **no direct in-app scenario modeling** component in the initial release. Instead, enable users to **upload scenario results** (e.g., climate stress tests) as supporting documents or comments linked to relevant IROs.

**Justification:**  
- **Simplicity**: Focuses the software on robust Double Materiality record-keeping rather than complex forecasting engines.  
- **Flexibility**: Organizations can use specialized climate or regulatory modeling tools and attach results as evidence.  
- **Scalability**: Deferring advanced scenario features reduces initial complexity while still accommodating scenario data.

---

### **Question 5**  
**What mechanisms should be in place to capture short-term or emerging “flash” risks within the Double Materiality framework?**

**Recommended Solution:**  
Retain **annual core updates** but designate a process to flag “interim exceptions” for short-term or urgent risks. These exceptions require a **separate management sign-off**, ensuring they are visible and tracked outside the normal cycle.

**Justification:**  
- **Practicality**: Preserves a predictable update rhythm while addressing urgent developments.  
- **Accountability**: Requiring a special sign-off raises visibility for flash risks among senior stakeholders.  
- **Documentation**: Clear records of interim changes reduce confusion and support audits.

---

### **Question 6**  
**How should stakeholder engagement be structured to enhance data quality and comprehensiveness in the Double Materiality Assessment process?**

**Recommended Solution:**  
Create a **digital stakeholder portal** where approved external or internal stakeholders can submit IRO insights, feedback, or supporting evidence. Integrate these inputs directly into the DMA platform for review and incorporation.

**Justification:**  
- **Automation**: Streamlines capturing new issues or validations directly from stakeholders.  
- **Traceability**: Each submission is timestamped and linked to a stakeholder, clarifying influence on final assessments.  
- **Inclusiveness**: Encourages continuous collaboration with key groups, improving the scope and accuracy of data.

---

### **Question 7**  
**How can the assessment framework handle multi-tier supply chains to ensure a robust analysis of Impact Materiality across all relevant suppliers and partners?**

**Recommended Solution:**  
Enable **value-chain tagging** within each IRO, allowing users to specify which part of the supply chain (upstream/downstream tiers) a risk or impact applies to. For deeper complexity, allow linking multiple tiers under a single IRO to track extended supply chain impacts.

**Justification:**  
- **Comprehensive Coverage**: Recognizes that major impacts often occur beyond direct Tier-1 suppliers.  
- **Granularity**: Tier-specific tagging helps isolate where key risks or opportunities lie.  
- **Scalability**: The model can expand as more supply-chain data becomes available.

---

### **Question 8**  
**What is the best approach to integrating external ESG or GHG emissions data sources into the Double Materiality system architecture?**

**Recommended Solution:**  
Use **manual CSV/Excel uploads** on a quarterly or annual basis, ensuring data is reviewed before ingestion. Provide clear templates and validation rules to maintain data quality.

**Justification:**  
- **Simplicity & Reliability**: Avoids building (and maintaining) complex, real-time integration pipelines early on.  
- **Data Governance**: Manual review ensures correctness, which is critical for official disclosures.  
- **Scalability**: The approach can evolve to APIs or automated feeds later if the organization’s data maturity increases.

---

## **2. Data Architecture**

---

### **Question 9**  
**What is the optimal approach for storing and managing assessment evidence (e.g., documents, images) linked to IROs?**  

**Recommended Solution:**  
Use **Amazon S3** for file storage with versioning enabled and store **metadata references** (e.g., document path, upload date) in a relational table (e.g., Amazon RDS).

**Justification:**  
- **Scalability & Cost**: S3 easily handles large files, supports lifecycle rules, and offers low-cost storage.  
- **Auditability**: Versioning in S3 plus references in RDS facilitate traceability of document changes.  
- **Performance**: Keeping only references in the main DB avoids bloating the primary transactional tables.

---

### **Question 10**  
**How should the system handle data integration with existing ESG systems?**  

**Recommended Solution:**  
Support **file-based imports** (e.g., CSV or Excel) for bulk or historical data loads and selectively build **API/ETL connectors** for ESG platforms that offer stable, well-documented endpoints.

**Justification:**  
- **Immediate Practicality**: Many ESG solutions still rely on file transfers, especially for older or custom systems.  
- **Scalable Evolution**: Allows incremental API integrations for organizations with more modern infrastructure.  
- **Flexibility**: Users can choose whichever integration method suits their existing processes.

---

### **Question 11**  
**How should the solution handle the storage of granular Impact Materiality and Financial Materiality scoring data?**  

**Recommended Solution:**  
Create **dedicated child tables** or structured JSON columns to store each dimension (scale, scope, likelihood, magnitude). Reference them from a main “assessments” table with proper foreign keys.

**Justification:**  
- **Clarity**: Separating these details prevents overloading the main table with too many columns.  
- **Flexibility**: New criteria or scoring adjustments can be added without disruptive schema overhauls.  
- **Query Performance**: Well-designed foreign keys or indexed JSON fields simplify retrieving specific criteria.

---

### **Question 12**  
**What is the best strategy for archiving older IRO records and their assessments while still retaining accessibility for audit or compliance checks?**  

**Recommended Solution:**  
After a defined retention period (e.g., 3–5 years), migrate older IRO data into **Amazon S3 with Glacier** for cost-effective long-term storage. Maintain a **minimal reference** in the primary database for quick lookups or retrieval requests.

**Justification:**  
- **Cost Efficiency**: Glacier storage is cheaper than keeping stale records in a high-performance DB.  
- **Compliance**: S3 versioning and retrieval logs ensure robust audit trails.  
- **Performance**: Reduces operational load on the main database while preserving direct access to archived data.

---

### **Question 13**  
**Which data model strategy is most appropriate for storing and linking IRO records with their respective Double Materiality Assessments?**  

**Recommended Solution:**  
Use **normalized relational tables**: an `IRO` table for base info, `Assessments` for double materiality results, plus optional child tables (e.g., `ImpactMateriality`, `FinancialMateriality`). Use **foreign keys** to link them.

**Justification:**  
- **Data Integrity**: Relationships are enforced via primary/foreign key constraints.  
- **Maintainability**: Easier to query and maintain, especially for compliance or auditing.  
- **Extensibility**: Additional attributes or new criteria can be accommodated without radical schema changes.

---

### **Question 14**  
**How should the platform manage multi-tenancy at the database level to ensure data isolation and scalability?**  

**Recommended Solution:**  
Adopt a **multi-tenant architecture** using either:  
1) **Separate schemas** in a single database for most tenants, enforcing row- or schema-level security, and  
2) **Dedicated database instances** for larger or highly regulated clients who need maximum isolation.

**Justification:**  
- **Cost-Effectiveness**: A single database with multiple schemas is simpler and cheaper for standard tenants.  
- **Flexibility**: High-compliance or big-volume tenants can be moved to dedicated instances.  
- **Scalability**: Supports a wide range of tenant needs without overcomplicating the core design.

---

### **Question 15**  
**How should we design the data model to accommodate stakeholder feedback at multiple levels (e.g., local site teams, CSR committees, board-level reviews) without causing schema bloat or redundant records?**

**Recommended Solution:**  
Create a set of **normalized feedback tables** (e.g., `Feedback`, `StakeholderGroup`, `FeedbackDetail`), each linked to the relevant IRO or assessment record via foreign keys.

**Justification:**  
- **Minimal Redundancy**: Centralizes feedback attributes, avoids duplicating columns across many tables.  
- **Data Integrity**: Relational links prevent confusion about which feedback belongs to which stakeholder or IRO.  
- **Scalability**: Adding new feedback categories or hierarchical levels is straightforward in a well-normalized model.

---

### **Question 16**  
**What is the best method for ingesting near real-time environmental or financial metrics (e.g., energy consumption, carbon footprints) into the DMA platform?**

**Recommended Solution:**  
*(Currently not in scope.)* The platform does not initially offer near real-time ingestion. Focus instead on **periodic file-based or API-driven imports** at scheduled intervals.

**Justification:**  
- **Complexity Control**: Real-time data pipelines (streaming, message queues) significantly increase architectural complexity.  
- **Practical Frequency**: Most sustainability metrics are updated monthly or quarterly, so daily or weekly batches suffice.  
- **Future Expandability**: The design can evolve to real-time ingestion once there is a clear business case.

---

### **Question 17**  
**How should the system handle on-demand analytics (e.g., financial stress tests, scenario modeling) that require aggregating large volumes of assessment data?**

**Recommended Solution:**  
*(Currently not in scope.)* The DMA platform will not include built-in large-scale stress-testing modules. Export data to specialized analytics tools or data warehouses when advanced modeling is required.

**Justification:**  
- **Simplicity**: Keeps the core platform lightweight and focused on Double Materiality record-keeping.  
- **Best-of-Breed**: Specialized analytics software is better suited for complex scenario modeling.  
- **Modularity**: Export-based integration ensures future flexibility in choosing analytics or BI platforms.

---

### **Question 18**  
**What strategy should be used to integrate external ESG or sustainability frameworks (e.g., GRI, SASB, TCFD) so that their data can be leveraged for a comprehensive Double Materiality Assessment?**

**Recommended Solution:**  
*(Currently not in scope.)* No direct framework-to-framework integration at first. Provide **mapping guides** for users to align GRI/SASB/TCFD data fields with the IRO structure, typically via manual or CSV-based imports.

**Justification:**  
- **Avoid Overcomplication**: Handling each framework’s variations in real time is complex.  
- **User Flexibility**: Many organizations already have partial data or specialized consultants for these frameworks.  
- **Incremental Approach**: Start with a generic import method; refine or automate mapping if enough demand arises.

---

### **Question 19**  
**How should the platform manage integration with external financial systems (e.g., ERP, accounting software) to correlate sustainability metrics with actual financial performance?**

**Recommended Solution:**  
*(Currently not in scope.)* Rely on periodic or on-demand **manual data exports** from the ERP or financial system in a structured format (CSV/Excel). Upload these files into the DMA platform for reference or correlation.

**Justification:**  
- **Lower Risk**: Building real-time ERP integrations requires significant engineering and governance overhead.  
- **Incremental**: Start with manual ingestion to gauge usage before investing in tight ERP API integrations.  
- **Data Validation**: Manual reviews or approvals help ensure data accuracy before linking to IROs.

---

### **Question 20**  
**How can we securely expose the DMA platform’s data resources to external clients, enabling them to read and update their IRO records via an API?**

**Recommended Solution:**  
Use **OAuth 2.0** (e.g., via Amazon Cognito) with short-lived tokens and apply granular Role-Based Access Control (RBAC). Validate all tokens at the API Gateway and combine this with database-level row- or schema-level security.

**Justification:**  
- **Standards-Based**: OAuth 2.0 is widely recognized and integrates smoothly with AWS services.  
- **Granular Security**: Fine-grained RBAC plus row-level security ensures each client sees only their own data.  
- **Scalability**: The token-based approach handles high traffic while staying secure and compliant.

---

### **Question 21**  
**What measures can we implement to ensure that only authorized external clients can programmatically manipulate assessment data without introducing undue complexity?**

**Recommended Solution:**  
Use **short-lived, fine-grained OAuth 2.0 access tokens** enforced by AWS API Gateway. Each token is scoped to specific operations (read/write) and must be renewed frequently.

**Justification:**  
- **Reduced Risk Window**: Short expiry tokens limit the impact of compromised credentials.  
- **Centralized Authorization**: API Gateway is a single choke point for validating tokens and applying usage rules.  
- **Compliance**: Detailed logs of token issuance and usage satisfy CSRD/GDPR security requirements.

---

### **Question 22**  
**How can the DMA platform maintain stable, secure, and backward-compatible API endpoints for clients who integrate deeply with the system over time?**

**Recommended Solution:**  
Adopt a **versioned REST API** strategy (e.g., `/api/v1/` and `/api/v2/`) with clear deprecation policies and robust documentation. Provide a transition window before retiring older versions.

**Justification:**  
- **Predictability**: Clients can safely rely on a stable version without sudden breaking changes.  
- **Maintainability**: Versioning isolates new features or breaking updates from existing consumers.  
- **Transparency**: A published deprecation schedule helps external developers plan updates proactively.

---

### **Question 23**  
**How should we automate tenant onboarding in a multi-tenant SaaS environment to minimize manual intervention and ensure consistent setup workflows?**

**Recommended Solution:**  
Use a **self-service registration process** that triggers an **event-driven provisioning pipeline** (AWS Lambda or Step Functions) to set up tenant resources (schemas, default roles, initial user accounts) in a standardized way.

**Justification:**  
- **Consistency**: Automated pipelines eliminate human error and ensure each new tenant is configured uniformly.  
- **Scalability**: Event-driven workflows handle spikes in sign-ups without manual bottlenecks.  
- **Extendibility**: Additional tasks (e.g., generating sample data) can be appended to the pipeline with minimal effort.

---

### **Question 24**  
**What is the most efficient strategy for managing tenant lifecycle events (e.g., suspending, reactivating, or offboarding tenants) while adhering to compliance requirements?**

**Recommended Solution:**  
Develop a **central “Tenant Lifecycle” microservice** with dedicated endpoints for each event (activate, suspend, offboard). Update tenant status in the database and systematically restrict or restore access.

**Justification:**  
- **Single Source of Truth**: All lifecycle logic is in one place, simplifying audits and debugging.  
- **Data Integrity**: Suspended tenants keep their data intact (just restricted), ensuring compliance with CSRD record-keeping.  
- **Modular**: Any other service (billing, user access) can listen for lifecycle events and respond accordingly.

---

### **Question 25**  
**How can we optimize database isolation for tenants who require more stringent performance or compliance guarantees without introducing unnecessary complexity for all tenants?**

**Recommended Solution:**  
Use a **hybrid model**. Most tenants share a single database (with separate schemas or row-level security), whereas premium or highly regulated tenants receive a **dedicated database instance** or cluster.

**Justification:**  
- **Cost Efficiency**: Simple shared infrastructure serves most tenants well.  
- **Enhanced Isolation**: Critical clients avoid “noisy neighbor” issues and meet strict compliance demands.  
- **Flexibility**: Allows the SaaS to serve both SMBs and large enterprises under one architecture.

---

### **Question 26**  
**Which approach should be used to provide tenant-specific customizations (e.g., branding, feature toggles) without complicating the core codebase?**

**Recommended Solution:**  
Store **configuration metadata** (branding preferences, feature flags) in a central `tenant_config` table keyed by `tenant_id`. Load these settings at runtime to dynamically adjust UI or features.

**Justification:**  
- **Clean Separation**: Core logic remains the same; only the presentation or feature availability changes by tenant config.  
- **Maintainability**: New customization fields can be added easily in a single table, avoiding code fragmentation.  
- **Auditability**: A single source of truth for customizations simplifies tracking changes and diagnosing issues.

---

### **Question 27**  
**How can we ensure that automated tenant onboarding and lifecycle management processes remain resilient and recover gracefully from exceptions or partial failures?**

**Recommended Solution:**  
Use **idempotent, event-driven workflows** with **compensating transactions**. If any provisioning step fails, the workflow can roll back changes or retry safely without duplicating partial resources.

**Justification:**  
- **Data Consistency**: Eliminates orphaned records or incomplete setups in the event of failure.  
- **Reliability**: Automatic retries and rollback steps ensure a stable onboarding experience.  
- **Compliance**: Well-defined workflows with full logging simplify audits and error tracing.

---

### **Question 28**  
**How should the DMA platform store billing details for subscription-based usage (e.g., plan tiers, usage limits, payment history) without overcomplicating the core Double Materiality data model?**

**Recommended Solution:**  
Integrate with a **specialized billing service** (e.g., Stripe, Chargebee) for complex financial transactions, while storing **minimal references** (subscription ID, plan type, usage tier) in the main RDS.

**Justification:**  
- **Separation of Concerns**: Offloads tax logic, invoicing, and payment processing to experts.  
- **Reduced Complexity**: Maintains a lean schema in the DMA database.  
- **Global Compliance**: Third-party billing platforms often handle region-specific regulations out of the box.

---

### **Question 29**  
**What is the best approach for managing invoicing data—such as invoice generation, tracking, and adjustments—associated with multiple tenant accounts in the platform?**

**Recommended Solution:**  
Keep a **lightweight “Invoices” table** in the DMA database for invoice metadata (e.g., invoice number, date, amount) linked to each tenant. Any advanced accounting or tax calculations remain in the external billing service.

**Justification:**  
- **Immediate Visibility**: The DMA platform can show invoice status/history for each tenant.  
- **Delegation of Complexity**: Detailed financial processes (tax rates, payment gateways) stay external.  
- **Scalable**: If more sophisticated invoicing features are needed, the external billing engine can handle them.

---

### **Question 30**  
**How can the platform handle refunds, credits, or returns on billed amounts (e.g., if a tenant overpays or opts out mid-cycle) without disrupting the core Double Materiality Assessment workflows?**

**Recommended Solution:**  
Use a **separate “Refund/Adjustment” table** referencing the original invoice record. Store refund amounts, dates, and rationale. Reflect this in the tenant’s billing status but keep the original invoice intact.

**Justification:**  
- **Audit Trail**: Ensures refunds or credits don’t overwrite original financial records.  
- **Transparency**: Adjustments are tracked independently, aligning with standard accounting practices.  
- **Simplicity**: The Double Materiality data remains unaffected, preventing confusion around core assessment records.

---

## **3. User Interface**

---

### **Question 31**  
**What is the most effective way to present materiality assessment results to decision-makers?**  

**Recommended Solution:**  
Display a **2x2 materiality matrix** (impact severity vs. financial magnitude) as a high-level dashboard, and allow **drill-down** into heatmaps or tabular views of underlying IRO details.

**Justification:**  
- **Clarity**: Executives quickly grasp a 2x2 chart for prioritization.  
- **Depth**: Sustainability teams need more granular data—drill-down views deliver that detail.  
- **Adoption**: Familiar matrix visuals facilitate faster user acceptance.

---

### **Question 32**  
**How should the system handle collaborative assessment workflows for multiple reviewers or roles?**  

**Recommended Solution:**  
Implement a **configurable workflow engine** with sequential and parallel review steps. For example, items can progress from “Draft” → “In Review” → “Approved” → “Disclosed.” Allow **conditional routing** for high-severity IROs.

**Justification:**  
- **Flexibility**: Different organizations have varying governance processes.  
- **Accountability**: Each stage logs who reviewed/approved the record.  
- **Scalability**: Workflows can adapt to complex sign-off paths without major code changes.

---

### **Question 33**  
**What UI approach should be taken to accommodate various user roles (Sustainability Manager, CFO, Auditor, etc.) for Double Materiality Assessments?**  

**Recommended Solution:**  
Create a **unified interface** that applies **role-based access controls** (RBAC) to show or hide functionalities. Offer **role-specific “home” pages** so each user sees the data and KPIs most relevant to them upon login.

**Justification:**  
- **Efficiency**: A single codebase, but personalized experiences.  
- **Security**: RBAC ensures no user inadvertently sees data beyond their permissions.  
- **User Experience**: Minimizes confusion and highlights priority tasks or metrics.

---

### **Question 34**  
**How should the system represent and guide users through Impact vs. Financial Materiality in the UI?**  

**Recommended Solution:**  
Use a **step-by-step wizard** for data input:  
1) Collect Impact Materiality details (scope, scale, likelihood).  
2) Collect Financial Materiality details (magnitude, likelihood).  
Afterward, display a **combined Double Materiality summary** (e.g., matrix or aggregated scoring).

**Justification:**  
- **Ease of Use**: Breaking input into smaller steps is less overwhelming.  
- **Completeness**: Ensures both impact and financial dimensions are consistently assessed.  
- **Transparency**: The final overview clarifies how each dimension contributed to the overall conclusion.

---

### **Question 35**  
**What approach should be used to guide non-expert users through the DMA process (e.g., identifying IROs, setting severity, etc.)?**  

**Recommended Solution:**  
Implement a **wizard-style interface** with **mandatory fields** at each stage and **contextual tooltips** explaining technical terms. Optionally integrate a **chatbot** or help widget for just-in-time guidance.

**Justification:**  
- **Reduced Errors**: Mandatory prompts minimize incomplete data.  
- **User Confidence**: Clear help text or a chatbot reduces confusion about sustainability jargon.  
- **Accessibility**: Even small organizations with minimal sustainability expertise can complete assessments confidently.

---

### **Question 36**  
**How should final reports (aligned with ESRS requirements) be generated and shared with stakeholders?**  

**Recommended Solution:**  
Allow on-demand **PDF or Excel exports**, stored securely in the system. Provide **role-based permissions** for downloading or distributing these reports, plus the option to share via **secure links** or an **API** (for third-party compliance tools).

**Justification:**  
- **Universality**: PDF/Excel are standard formats accepted by boards, regulators, and auditors.  
- **Security**: Role-based controls ensure sensitive data goes only to authorized parties.  
- **Integration**: Exposing a REST API or secure link supports external compliance reviews or data rooms.

---

## **4. Compliance**

---

### **Question 37**  
**Which security and privacy frameworks should be prioritized to align with EU CSRD and stakeholder expectations?**  

**Recommended Solution:**  
Implement **SOC 2 Type II** controls for operational security and **GDPR** compliance for personal data. Add **ESRS-specific** checks on sustainability data integrity (e.g., verifying authenticity of ESG metrics).

**Justification:**  
- **SOC 2** addresses confidentiality, integrity, and availability—key for trust.  
- **GDPR** is mandatory for handling EU personal data.  
- **ESRS** alignment ensures consistent, transparent reporting on sustainability metrics.

---

### **Question 38**  
**How should the system handle audit trails to demonstrate compliance with ESRS reporting and internal governance?**  

**Recommended Solution:**  
Use a **comprehensive audit log** (or event-sourcing approach) capturing every state change (who, what, when). Store critical logs in **immutable storage** (e.g., versioned S3 or an append-only ledger).

**Justification:**  
- **Traceability**: Full history of changes supports internal investigations and external audits.  
- **Tamper Resistance**: Immutable or append-only logs protect the integrity of the audit trail.  
- **Transparency**: Clearly documents how data evolved over time, meeting CSRD/ESRS evidence needs.

---

### **Question 39**  
**What should be the policy for disclosing non-material IROs under CSRD guidelines if stakeholders request them?**  

**Recommended Solution:**  
Provide a **configurable toggle** to include/exclude non-material IROs in the main report. Offer a **“full list” export** if a deeper level of disclosure is requested by certain stakeholders.

**Justification:**  
- **Flexibility**: Not all organizations want to clutter primary reports with non-material items.  
- **Transparency**: The optional “full list” meets stakeholder demands for openness.  
- **Regulatory Respect**: CSRD focuses on material items but does not prohibit additional voluntary disclosure.

---

### **Question 40**  
**How can we demonstrate that stakeholder engagement processes (a key CSRD requirement) have been incorporated into the Double Materiality Assessment?**  

**Recommended Solution:**  
Include **fields or attachments** in each IRO record to document stakeholder input. Track **engagement events** (e.g., workshops, interviews) in a separate table referencing the relevant IROs.

**Justification:**  
- **Auditability**: Shows exactly when and how stakeholders contributed.  
- **Compliance**: Meets CSRD’s emphasis on inclusive materiality processes.  
- **Influence Trace**: Auditors or managers can see how engagement feedback changed the assessment outcomes.

---

### **Question 41**  
**Which mechanisms should be introduced to demonstrate alignment with ESRS guidelines and facilitate external audits?**  

**Recommended Solution:**  
Generate a **“DMA + ESRS Mapping”** report that correlates IRO data and Double Materiality results to each relevant ESRS disclosure requirement. Implement a **compliance checklist** within the platform that flags any missing mandatory data.

**Justification:**  
- **Clear Mapping**: Auditors can see how each ESRS requirement is addressed by specific data points.  
- **Internal Readiness**: The checklist ensures no key ESRS sections are overlooked before formal reporting.  
- **Simplified Audits**: A direct cross-reference accelerates external assurance or verification processes.

---

</consolidated Q&A bank>

<architectural design document>
## 1. Executive Summary

This document proposes an **AWS-hosted, multi-tenant SaaS architecture** that aligns with the **AWS Well-Architected Framework** (covering **Security**, **Reliability**, **Performance Efficiency**, **Cost Optimization**, and **Operational Excellence**). The goal is to deliver a **secure**, **scalable**, and **cost-effective** application for multiple tenants while ensuring **stringent data isolation** and compliance with relevant standards (e.g., GDPR, SOC 2, industry-specific regulations).

This design accommodates:
- **Tenant isolation** via logical or physical segmentation.
- **Centralized authentication and authorization** through Amazon Cognito and AWS IAM best practices.
- **Highly available** and **fault-tolerant** microservices and databases.
- **Monitoring and observability** using AWS-native services (Amazon CloudWatch, AWS X-Ray).
- **Phased cost optimization** to ensure resources match usage and budget targets.

---

## 2. System Requirements and Constraints

### 2.1 Functional Requirements
1. **Multi-Tenant Support**  
   - Segregated data per tenant  
   - Ability to onboard new tenants rapidly  

2. **Secure & Compliant**  
   - End-to-end encryption (in transit, at rest)  
   - Centralized identity management with MFA  
   - Audit logging for compliance (GDPR, SOC 2, etc.)  

3. **Scalable & Highly Available**  
   - Auto-scaling for peak loads  
   - Multi-AZ or multi-region failover options  

4. **API-Driven**  
   - RESTful APIs with versioning  
   - Tenant-level usage analytics and rate limiting  

### 2.2 Non-Functional Requirements
1. **Performance**  
   - Sub-second latency for typical read/write operations  
   - Ability to handle large data volumes (tens of millions of records)  

2. **Reliability**  
   - 99.9% SLA or better for critical paths  
   - Automated backups and disaster recovery strategy  

3. **Maintainability**  
   - Infrastructure as Code (IaC) approach (CloudFormation / CDK / Terraform)  
   - Clear separation of concerns between microservices  

4. **Cost Constraints**  
   - Optimize for pay-as-you-grow with minimal overhead for small tenants  
   - Expand capacity with usage or enterprise-tier growth  

5. **Compliance & Auditing**  
   - Configurable data retention policies  
   - Detailed user and admin activity logs  

---

## 3. Architecture Overview

### 3.1 High-Level Diagram

Below is a high-level **ASCII architecture diagram** illustrating the major AWS components and data flow.

```
                   ┌─────────────┐
                   │   Amazon    │
                   │   Route 53  │
                   └──────▲──────┘
                          │
                    ┌─────┴─────┐
                    │  Amazon   │
                    │ CloudFront│
                    └─────▲─────┘
                          │
                    ┌─────┴─────┐     ┌───────────────┐
   Internet  ─────>  │   AWS WAF  │ -->│ AWS Shield (Opt)│
                    └─────┬─────┘     └───────────────┘
                          │
                    ┌─────┴─────┐
                    │ API Gateway│
                    └─────┬─────┘
                          │
                  ┌───────┴───────────┐
                  │ AWS Fargate/ECS   │
                  │  (Microservices)  │
                  └───────┬───────────┘
                          │
                ┌─────────┴─────────┐
                │ Amazon RDS (PostgreSQL) │
                │  (Multi-tenant DB) │
                └─────────┬─────────┘
                          │
             ┌────────────┴─────────────┐
             │   Amazon S3 (Audit/Logs) │
             └──────────────────────────┘

   ┌─────────────────────────┐
   │    Amazon Cognito       │
   │ (AuthN/AuthZ, MFA, SSO) │
   └─────────────────────────┘
```

### 3.2 Key Components

1. **Amazon Route 53 & Amazon CloudFront**  
   - Custom domain resolution, optional CDN for static assets and API caching.  

2. **AWS WAF & AWS Shield**  
   - Web Application Firewall to defend against common exploits.  
   - Shield Standard or Advanced (depending on threat level) for DDoS mitigation.  

3. **Amazon API Gateway**  
   - Front door for all REST APIs, usage plans, throttle limits, and authentication integration.  

4. **AWS Fargate (ECS)**  
   - Container orchestration with minimal overhead.  
   - Host microservices (e.g., tenant management, core application logic).  

5. **Amazon RDS (PostgreSQL)**  
   - Primary transactional store with row-level security or separate schemas for tenant isolation.  

6. **Amazon S3**  
   - Stores large files, audit logs, and backups.  
   - Versioning enabled for immutability of logs.  

7. **Amazon Cognito**  
   - Centralized identity provider for multi-tenant user pools.  
   - MFA, SSO, fine-grained identity and access control.  

### 3.3 Data Flow

1. **External Client / Tenant Request** enters via Route 53 → CloudFront → WAF → API Gateway.  
2. **API Gateway** authorizes requests using **Cognito JWT tokens** and forwards valid requests to Fargate-based microservices.  
3. **Microservices** process requests, apply tenant-specific logic, and communicate with the **RDS** backend.  
4. **RDS** enforces row-level security or separate schema constraints, returning only tenant-specific data.  
5. **Logs** and **audit trails** are forwarded to Amazon S3 (versioned) or CloudWatch for compliance and analytics.  
6. **Monitoring** and metrics are collected by Amazon CloudWatch and AWS X-Ray for distributed tracing.

---

## 4. Detailed Component Design

### 4.1 Tenant Isolation Strategy

- **Primary Approach**: Single RDS cluster with either  
  - **Row-Level Security (RLS)** filtering by `tenant_id`, or  
  - **Separate Schemas** per tenant for heavier data partitioning.  
- **Premium Tier**: Dedicated RDS instance if compliance or throughput demands require fully isolated DB.  
- **Benefits**:  
  - RLS + proper IAM roles ensure minimal risk of cross-tenant data leakage.  
  - Easier to manage than multiple DB instances for smaller tenants.

### 4.2 Authentication and Authorization

- **Amazon Cognito** as the IDaaS solution:
  - **User Pools**: Manage tenant users, support SAML/OIDC for enterprise SSO.  
  - **Identity Pools (optional)**: Provide temporary AWS credentials for direct S3 uploads or other resources.  
- **Roles & Policies**: Fine-grained roles (e.g., Admin, Manager, Viewer) enforced within microservices and RLS.  
- **MFA**: Strongly recommended for all privileged accounts.  
- **JWT Validation**: API Gateway checks token claims before routing traffic to microservices.  

### 4.3 Data Layer Design

1. **Amazon RDS (PostgreSQL)**  
   - **Multi-AZ** for high availability.  
   - **Point-in-time recovery** and automated backups.  
   - **Encryption at rest** (KMS) and in transit (TLS).  
   - **RLS** policies or separate schemas for multi-tenant.  

2. **Amazon S3**  
   - **Versioned buckets** for audit logs, compliance data.  
   - **Lifecycle policies** to transition old logs to Glacier for cost savings.  
   - **Server-side encryption** using AWS KMS.  

3. **Optional ElastiCache (Redis)**  
   - Caching layer to offload read traffic from the DB.  
   - Helps with frequently accessed tenant-specific data or session info (if not using Cognito tokens).

### 4.4 API Layer Architecture

- **Amazon API Gateway** (REST or HTTP APIs):
  - **Custom usage plans** per tenant or per role.  
  - **Rate limiting** to prevent misuse and DOS attacks.  
  - **Stage variables** for versioning (e.g., `/v1`, `/v2`).  
- **Integration with AWS Fargate**:
  - **Private integration** or via an internal ALB to keep traffic within VPC.  
- **Deployment Pipeline**:
  - **CI/CD** (AWS CodePipeline or GitHub Actions) triggers build/test.  
  - Automated integration tests and canary deployments.

### 4.5 Monitoring and Observability

- **Amazon CloudWatch**  
  - Collects logs (application logs, access logs) and system metrics (CPU, memory).  
  - Custom dashboards for tenant usage tracking.  
- **AWS X-Ray**  
  - Distributed tracing across microservices.  
  - Pinpoints latency or error rates by tenant or endpoint.  
- **Amazon GuardDuty & Security Hub**  
  - Monitors and aggregates security findings across the AWS environment.  
- **Metrics & Alerts**  
  - CloudWatch Alarms on RDS CPU usage, Fargate container health, API Gateway 4xx/5xx errors.  
  - Automated notification (SNS, Slack, or email) for threshold breaches.

---

## 5. Security Considerations

1. **Encryption**  
   - **KMS** for database and S3 encryption.  
   - SSL/TLS for all inbound traffic (HTTPS), including internal service calls.  
2. **Least Privilege IAM**  
   - Microservices use **minimal IAM roles** with access only to required resources (S3 bucket, RDS secrets).  
   - Restrictive **Security Groups** to limit east-west traffic.  
3. **Web Application Firewall (WAF)**  
   - Rules for SQL injection, XSS, IP reputation blocking.  
4. **AWS Shield**  
   - **Shield Standard** for baseline DDoS protection (upgradable to **Advanced** if needed).  
5. **Audit Trails**  
   - CloudTrail for AWS-level API calls.  
   - Application-level logging with user action details (create/update/delete events).  
   - Store logs in **immutable** S3 buckets (versioning + write-once, read-many if needed).  
6. **Secure Secret Management**  
   - **AWS Secrets Manager** for DB credentials and API keys.  
   - Automated rotation for credentials where feasible.

---

## 6. Scalability and Performance

1. **Compute Scaling**  
   - **AWS Fargate** services autoscale based on CPU/memory or custom CloudWatch metrics (request count, queue depth).  
   - Additional containers spin up as traffic grows, spin down in off-peak times.  

2. **Database Scaling**  
   - **Vertical scaling** of RDS instance type.  
   - **Read replicas** for read-heavy workloads, or if multi-region read access is required.  

3. **Storage Tiering**  
   - S3 + Glacier for cold data storage.  
   - Lifecycle policies to automatically move less-used logs to cheaper storage.  

4. **Network & Global Distribution**  
   - **Amazon CloudFront** to reduce latency for static assets.  
   - Potential **multi-region** replication for disaster recovery or low-latency global coverage.  

5. **Caching**  
   - **ElastiCache (Redis)** for session or frequently accessed data.  
   - **API Gateway** caching for certain endpoints if read patterns are consistent.  

---

## 7. Cost Optimization

1. **Serverless & Fargate**  
   - Pay only for actual container runtime.  
   - Avoid overhead of idle servers.  
2. **RDS Right-Sizing**  
   - Start with smaller instance types; scale up as tenants increase or usage grows.  
   - Evaluate **Reserved Instances** or **Savings Plans** if usage is predictable.  
3. **S3 Storage Classes**  
   - Use **Intelligent-Tiering** or **Glacier** for older data.  
   - Versioning carefully to avoid excess storage of changed files.  
4. **Optimize Data Retention**  
   - Archive logs after a set retention period.  
   - Limit row-level detail in S3 if summary logs suffice.  
5. **Monitor Billing**  
   - Use **AWS Budgets** and **Cost Explorer** for real-time cost tracking.  
   - Tag resources (by tenant, environment) for detailed cost attribution.

---

## 8. Implementation Recommendations

1. **Phase 1: Core Multi-Tenant Foundation**  
   - Set up single PostgreSQL instance (Multi-AZ) with row-level security or separate schemas.  
   - Deploy microservices to **AWS Fargate** with a minimal set of containers (web/API, worker).  
   - Integrate Amazon Cognito for tenant user authentication.  
   - Enable CloudWatch and basic WAF rules.  

2. **Phase 2: Security & Feature Enhancements**  
   - Expand to advanced WAF rules, guard against bots or advanced threats.  
   - Introduce **ElastiCache** if performance metrics show DB stress.  
   - Implement advanced user roles, custom usage metrics, and tenant-level dashboards.  

3. **Phase 3: Horizontal/Global Scaling**  
   - Implement **read replicas** or cross-region RDS for global low-latency.  
   - Use **CloudFront** with custom edge logic if content distribution is needed.  
   - Evaluate **AWS Shield Advanced** if the application faces persistent DDoS threats.  

4. **DevOps & Automation**  
   - Use **AWS CodePipeline** or Terraform to maintain Infrastructure as Code.  
   - Automatic blue-green or canary deployments.  
   - Integrate security scanning (SAST/DAST) in the pipeline for container images and code.  

5. **Ongoing Monitoring and Refinement**  
   - Continually tune auto-scaling policies and WAF rules.  
   - Regularly audit IAM roles, guardrail policies in AWS Organizations.  
   - Perform DR drills to test RDS backups and restore times.

---

### Final Notes

By implementing **AWS best practices**—including robust tenant isolation, centralized identity, and well-defined security boundaries—this **multi-tenant SaaS** architecture stands resilient, cost-efficient, and ready to scale. Adopting a phased approach ensures immediate business value with a secure, compliant foundation, while leaving room to evolve the platform as tenant counts and feature demands grow.
</architectural design document>


<design of user-facing views in Django>
Based on the provided solution design documents, here's a high-level summary of the key frameworks and modules recommended for building the main user-facing views in Django:

## Core Framework Stack

1. **View Layer**
- Django Class-Based Views (CBVs) for structured CRUD operations
- HTMX + Alpine.js for interactive features (lighter than React/Vue.js)
- django-formtools for multi-step wizards
- django-crispy-forms for form layouts

2. **Data Visualization**
- Chart.js + django-chartjs for materiality matrices and dashboards
- django-tables2 + django-filter for sortable data grids

3. **Authentication & Authorization**
- django-guardian for object-level permissions
- django-allauth for authentication (integrates with Amazon Cognito)

4. **API Integration**
- Django REST framework for API construction and documentation
</design of user-facing views in Django>

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

<log of last run>
(.venv) juanfuentes@MacBookPro IRO_platform % docker compose build                       
[+] Building 13.1s (20/21)                                                 docker:desktop-linux
 => [web internal] load build definition from Dockerfile                                   0.0s
 => => transferring dockerfile: 671B                                                       0.0s
 => [worker internal] load build definition from Dockerfile                                0.0s
 => => transferring dockerfile: 671B                                                       0.0s
 => [web internal] load metadata for docker.io/library/python:3.11-slim                    0.6s
 => [worker auth] library/python:pull token for registry-1.docker.io                       0.0s
 => [web internal] load .dockerignore                                                      0.0s
 => => transferring context: 2B                                                            0.0s
 => [worker internal] load .dockerignore                                                   0.0s
 => => transferring context: 2B                                                            0.0s
 => [web 1/6] FROM docker.io/library/python:3.11-slim@sha256:42420f737ba91d509fc60d5ed65e  0.1s
 => => resolve docker.io/library/python:3.11-slim@sha256:42420f737ba91d509fc60d5ed65ed049  0.1s
 => [worker internal] load build context                                                   0.9s
 => => transferring context: 1.56MB                                                        0.9s
 => [web internal] load build context                                                      0.9s
 => => transferring context: 1.56MB                                                        0.9s
 => CACHED [web 2/6] RUN apt-get update     && apt-get install -y postgresql-client     &  0.0s
 => CACHED [web 3/6] WORKDIR /app                                                          0.0s
 => CACHED [worker 4/6] COPY requirements.txt /app/                                        0.0s
 => CACHED [web 5/6] RUN pip install --no-cache-dir -r requirements.txt                    0.0s
 => [web 6/6] COPY . /app/                                                                 4.4s
 => CACHED [web 4/6] COPY requirements.txt /app/                                           0.0s
 => CACHED [web 5/6] RUN pip install --no-cache-dir -r requirements.txt                    0.0s
 => [worker] exporting to image                                                            6.8s
 => => exporting layers                                                                    3.7s
 => => exporting manifest sha256:cf1d610976ccf08aac023e2acc308be06e0109c0d1a9ddbc3a1bbeb0  0.0s
 => => exporting config sha256:7185509a9438817269dc02e152969c8160f6aca7352d536db1fa1bd67c  0.0s
 => => exporting attestation manifest sha256:0cb37dd3a6b0db6047ea939d5199ef0d28a1822da8b5  0.0s
 => => exporting manifest list sha256:829a76e93e62c7eec7971b58a54b2d65d9ea6ff8b18f2b05f4b  0.0s
 => => naming to docker.io/library/iro_platform-worker:latest                              0.0s
 => => unpacking to docker.io/library/iro_platform-worker:latest                           2.9s
 => [web] exporting to image                                                               6.8s
 => => exporting layers                                                                    3.7s
 => => exporting manifest sha256:ce64d9cf9158f11b6e3b43f954bc14023105e5714514f7b9c7a5a560  0.0s
 => => exporting config sha256:1cf8394441b30b5cab3581c40a157274540465b51ff0790c084daabb3f  0.0s
 => => exporting attestation manifest sha256:8e7e747b46413cae8a78785e7c894308d48d4378d255  0.0s
 => => exporting manifest list sha256:cf12067b292f77872bafb8c62c776f40f64c11871df95437166  0.0s
 => => naming to docker.io/library/iro_platform-web:latest                                 0.0s
 => => unpacking to docker.io/library/iro_platform-web:latest                              2.9s
 => [web] resolving provenance for metadata file                                           0.0s
 => [worker] resolving provenance for metadata file                                        0.0s
[+] Building 2/2
 ✔ web     Built                                                                           0.0s 
 ✔ worker  Built                                                                           0.0s 
(.venv) juanfuentes@MacBookPro IRO_platform % docker compose up
[+] Running 6/6
 ✔ Network iro_platform_default         Created                                            0.1s 
 ✔ Volume "iro_platform_postgres_data"  Created                                            0.0s 
 ✔ Container iro_platform-db-1          Created                                            0.4s 
 ✔ Container iro_platform-redis-1       Created                                            0.4s 
 ✔ Container iro_platform-worker-1      Created                                            0.2s 
 ✔ Container iro_platform-web-1         Created                                            0.2s 
Attaching to db-1, redis-1, web-1, worker-1
redis-1   | 1:C 20 Feb 2025 17:05:05.204 * oO0OoO0OoO0Oo Redis is starting oO0OoO0OoO0Oo
redis-1   | 1:C 20 Feb 2025 17:05:05.204 * Redis version=7.4.2, bits=64, commit=00000000, modified=0, pid=1, just started
redis-1   | 1:C 20 Feb 2025 17:05:05.204 # Warning: no config file specified, using the default config. In order to specify a config file use redis-server /path/to/redis.conf
redis-1   | 1:M 20 Feb 2025 17:05:05.207 * monotonic clock: POSIX clock_gettime
redis-1   | 1:M 20 Feb 2025 17:05:05.211 * Running mode=standalone, port=6379.
redis-1   | 1:M 20 Feb 2025 17:05:05.212 * Server initialized
redis-1   | 1:M 20 Feb 2025 17:05:05.212 * Ready to accept connections tcp
db-1      | The files belonging to this database system will be owned by user "postgres".
db-1      | This user must also own the server process.
db-1      | 
db-1      | The database cluster will be initialized with locale "en_US.utf8".
db-1      | The default database encoding has accordingly been set to "UTF8".
db-1      | The default text search configuration will be set to "english".
db-1      | 
db-1      | Data page checksums are disabled.
db-1      | 
db-1      | fixing permissions on existing directory /var/lib/postgresql/data ... ok
db-1      | creating subdirectories ... ok
db-1      | selecting dynamic shared memory implementation ... posix
db-1      | selecting default max_connections ... 100
db-1      | selecting default shared_buffers ... 128MB
db-1      | selecting default time zone ... Etc/UTC
db-1      | creating configuration files ... ok
db-1      | running bootstrap script ... ok
db-1      | performing post-bootstrap initialization ... ok
db-1      | syncing data to disk ... ok
db-1      | 
db-1      | 
db-1      | Success. You can now start the database server using:
db-1      | 
db-1      |     pg_ctl -D /var/lib/postgresql/data -l logfile start
db-1      | 
db-1      | initdb: warning: enabling "trust" authentication for local connections
db-1      | You can change this by editing pg_hba.conf or using the option -A, or
db-1      | --auth-local and --auth-host, the next time you run initdb.
db-1      | waiting for server to start....2025-02-20 17:05:06.687 UTC [47] LOG:  starting PostgreSQL 14.16 (Debian 14.16-1.pgdg120+1) on aarch64-unknown-linux-gnu, compiled by gcc (Debian 12.2.0-14) 12.2.0, 64-bit
db-1      | 2025-02-20 17:05:06.688 UTC [47] LOG:  listening on Unix socket "/var/run/postgresql/.s.PGSQL.5432"
db-1      | 2025-02-20 17:05:06.693 UTC [48] LOG:  database system was shut down at 2025-02-20 17:05:06 UTC
db-1      | 2025-02-20 17:05:06.699 UTC [47] LOG:  database system is ready to accept connections
db-1      |  done
db-1      | server started
db-1      | CREATE DATABASE
db-1      | 
db-1      | 
db-1      | /usr/local/bin/docker-entrypoint.sh: running /docker-entrypoint-initdb.d/01-init-schemas.sql
db-1      | CREATE TABLE
db-1      | CREATE FUNCTION
db-1      | INSERT 0 1
db-1      | INSERT 0 1
db-1      |  create_tenant_schema 
db-1      | ----------------------
db-1      |  
db-1      | (1 row)
db-1      | 
db-1      |  create_tenant_schema 
db-1      | ----------------------
db-1      |  
db-1      | (1 row)
db-1      | 
db-1      | 
db-1      | 
db-1      | waiting for server to shut down....2025-02-20 17:05:07.897 UTC [47] LOG:  received fast shutdown request
db-1      | 2025-02-20 17:05:07.898 UTC [47] LOG:  aborting any active transactions
db-1      | 2025-02-20 17:05:07.901 UTC [47] LOG:  background worker "logical replication launcher" (PID 54) exited with exit code 1
db-1      | 2025-02-20 17:05:07.902 UTC [49] LOG:  shutting down
db-1      | 2025-02-20 17:05:07.950 UTC [47] LOG:  database system is shut down
db-1      |  done
db-1      | server stopped
db-1      | 
db-1      | PostgreSQL init process complete; ready for start up.
db-1      | 
db-1      | 2025-02-20 17:05:08.028 UTC [1] LOG:  starting PostgreSQL 14.16 (Debian 14.16-1.pgdg120+1) on aarch64-unknown-linux-gnu, compiled by gcc (Debian 12.2.0-14) 12.2.0, 64-bit
db-1      | 2025-02-20 17:05:08.030 UTC [1] LOG:  listening on IPv4 address "0.0.0.0", port 5432
db-1      | 2025-02-20 17:05:08.030 UTC [1] LOG:  listening on IPv6 address "::", port 5432
db-1      | 2025-02-20 17:05:08.033 UTC [1] LOG:  listening on Unix socket "/var/run/postgresql/.s.PGSQL.5432"
db-1      | 2025-02-20 17:05:08.037 UTC [64] LOG:  database system was shut down at 2025-02-20 17:05:07 UTC
db-1      | 2025-02-20 17:05:08.041 UTC [1] LOG:  database system is ready to accept connections
web-1     | Checking for database availability...
web-1     | db:5432 - accepting connections
web-1     | Database is ready!
web-1     | Operations to perform:
web-1     |   Apply all migrations: admin, auth, contenttypes, sessions
web-1     | Running migrations:
web-1     |   Applying contenttypes.0001_initial... OK
web-1     |   Applying auth.0001_initial... OK
web-1     |   Applying admin.0001_initial... OK
web-1     |   Applying admin.0002_logentry_remove_auto_add... OK
web-1     |   Applying admin.0003_logentry_add_action_flag_choices... OK
web-1     |   Applying contenttypes.0002_remove_content_type_name... OK
web-1     |   Applying auth.0002_alter_permission_name_max_length... OK
web-1     |   Applying auth.0003_alter_user_email_max_length... OK
web-1     |   Applying auth.0004_alter_user_username_opts... OK
web-1     |   Applying auth.0005_alter_user_last_login_null... OK
web-1     |   Applying auth.0006_require_contenttypes_0002... OK
web-1     |   Applying auth.0007_alter_validators_add_error_messages... OK
web-1     |   Applying auth.0008_alter_user_username_max_length... OK
worker-1  | /usr/local/lib/python3.11/site-packages/celery/platforms.py:840: SecurityWarning: You're running the worker with superuser privileges: this is
worker-1  | absolutely not recommended!
worker-1  | 
worker-1  | Please specify a different user using the --uid option.
worker-1  | 
worker-1  | User information: uid=0 euid=0 gid=0 egid=0
worker-1  | 
worker-1  |   warnings.warn(SecurityWarning(ROOT_DISCOURAGED.format(
web-1     |   Applying auth.0009_alter_user_last_name_max_length... OK
web-1     |   Applying auth.0010_alter_group_name_max_length... OK
web-1     |   Applying auth.0011_update_proxy_permissions... OK
web-1     |   Applying auth.0012_alter_user_first_name_max_length... OK
web-1     |   Applying sessions.0001_initial... OK
worker-1  |  
worker-1  |  -------------- celery@44f01f812945 v5.2.7 (dawn-chorus)
worker-1  | --- ***** ----- 
worker-1  | -- ******* ---- Linux-6.12.5-linuxkit-aarch64-with-glibc2.36 2025-02-20 17:05:11
worker-1  | - *** --- * --- 
worker-1  | - ** ---------- [config]
worker-1  | - ** ---------- .> app:         core:0xffff948871d0
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
worker-1  | 
worker-1  | 
worker-1  | [2025-02-20 17:05:12,584: INFO/MainProcess] Connected to redis://redis:6379/0
worker-1  | [2025-02-20 17:05:12,586: INFO/MainProcess] mingle: searching for neighbors
web-1     | [2025-02-20 17:05:12 +0000] [9] [INFO] Starting gunicorn 20.1.0
web-1     | [2025-02-20 17:05:12 +0000] [9] [INFO] Listening at: http://0.0.0.0:8000 (9)
web-1     | [2025-02-20 17:05:12 +0000] [9] [INFO] Using worker: sync
web-1     | [2025-02-20 17:05:12 +0000] [10] [INFO] Booting worker with pid: 10
worker-1  | [2025-02-20 17:05:13,596: INFO/MainProcess] mingle: all alone
worker-1  | [2025-02-20 17:05:13,612: WARNING/MainProcess] /usr/local/lib/python3.11/site-packages/celery/fixups/django.py:203: UserWarning: Using settings.DEBUG leads to a memory
worker-1  |             leak, never use this setting in production environments!
worker-1  |   warnings.warn('''Using settings.DEBUG leads to a memory
worker-1  | 
worker-1  | [2025-02-20 17:05:13,612: INFO/MainProcess] celery@44f01f812945 ready.

</log of last run>