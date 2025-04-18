+-------------------------+      +-------------------------+      +-----------------------------+
|   1. Local Dev & Prep   |----->| 2. Containerize & Push  |----->|   3. Provision Core Infra   |
|-------------------------|      |-------------------------|      |-----------------------------|
| - Adapt code for AWS:   |      | - Build Docker images   |      | - Setup VPC & Subnets       |
|   - S3 (boto3)          |      |   (web, worker)         |      |   (Public/Private)          |
|   - RDS (SQLAlchemy)    |      | - Create ECR Repos      |      | - Configure Security Groups |
|   - ElastiCache (Redis) |      | - Authenticate Docker   |      | - Create S3 Bucket          |
|   - SES (boto3)         |      |   with ECR              |      | - Setup Secrets Manager     |
|   - Secrets Mgr/Env Vars|      | - Tag images            |      | - Setup SES (Verification)  |
| - Finalize Dockerfiles  |      | - Push images to ECR    |      |                             |
| - Update requirements.txt|      |                         |      |                             |
|   (add boto3, etc.)     |      |                         |      |                             |
|                         |      |                         |      |                             |
| PAIN POINTS:            |      | PAIN POINTS:            |      | PAIN POINTS:                |
| - Modifying code logic  |      | - Docker build issues   |      | - Complex Networking        |
| - Ensuring AWS SDKs are |      | - ECR auth failures     |      |   (Subnets, Routing)        |
|   correctly used        |      | - Large image sizes     |      | - Security Group rules      |
| - Local testing mock AWS|      | - Slow uploads          |      |   (Overly permissive/restrictive)|
|                         |      |                         |      | - IAM Permissions (Least    |
|                         |      |                         |      |   Privilege is hard)        |
|                         |      |                         |      | - SES domain verification   |
+-----------┬-------------+      +-----------┬-------------+      +--------------┬--------------+
            │                          │                                     │
            ▼                          ▼                                     ▼
+-------------------------+      +-------------------------+      +-----------------------------+
|  4. Provision Compute   |----->| 5. Deploy Application   |----->|  6. Operations & Monitor    |
|      & Services         |      |-------------------------|      |-----------------------------|
|-------------------------|      | - Create ECS Cluster    |      | - Setup CloudWatch Alarms   |
| - Provision RDS Instance|      |   (Fargate)             |      |   (CPU, Memory, Errors)     |
|   (e.g., PostgreSQL)    |      | - Create Task Defs      |      | - Monitor Logs (CW Logs)    |
| - Provision ElastiCache |      |   (web, worker)         |      | - Monitor Costs (Billing)   |
|   (Redis)               |      |   - Link ECR images     |      | - Backup Strategy (RDS, S3) |
| - Create App Load Balancer|      |   - Define resources    |      | - CI/CD Pipeline (Optional) |
|   (ALB)                 |      |   - Inject secrets (Env)|      |   (e.g., CodePipeline)      |
| - Configure Target Groups|      | - Create ECS Services   |      |                             |
|                         |      |   (web -> ALB, worker)  |      |                             |
|                         |      |   - Set desired counts  |      |                             |
|                         |      |   - Networking config   |      |                             |
|                         |      | - Point DNS to ALB      |      |                             |
|                         |      |                         |      |                             |
| PAIN POINTS:            |      | PAIN POINTS:            |      | PAIN POINTS:                |
| - Choosing correct      |      | - ECS Task Def errors   |      | - Log analysis complexity   |
|   instance sizes (Cost) |      |   (Syntax, Permissions) |      | - Alert fatigue/noise       |
| - DB/Cache connectivity |      | - Container startup fails|      | - Unexpected costs          |
|   from ECS              |      |   (Check CloudWatch Logs)|      | - CI/CD setup complexity    |
| - ALB health checks     |      | - Secrets not injected  |      | - Scaling configuration     |
|   failing               |      |   correctly             |      |   tuning                    |
| - IAM roles for tasks   |      | - Networking/SG issues  |      |                             |
|                         |      |   preventing connections|      |                             |
+-------------------------+      +-------------------------+      +-----------------------------+
