Below is a comprehensive **multi-tenant schema architecture** for an Enterprise SaaS solution on **AWS PostgreSQL**, carefully aligned with the **AWS Well-Architected Framework** and **GDPR/SOC2** compliance requirements. The solution follows **schema isolation**, incorporates **robust security**, supports **automated provisioning**, and addresses **horizontal scaling**. Please find the deliverable in the requested structured format:

---

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

---

#### 6. Usage Scenarios & Relationships

1. **IRO & DMAssessment**  
   - Each IRO can have **multiple** Double Materiality Assessments over time (e.g., periodic reassessments).  
   - `dm_assessment.iro_id → iro.iro_id`.  
2. **Review & Signoff**  
   - A **review** record tracks the process or stage of verifying an IRO.  
   - A **signoff** record references a completed review that has been **approved** or “signed.”  
   - Typically, a review or set of reviews must precede a signoff.  
3. **AuditTrail**  
   - Each table above logs changes into **audit_trail** (by table triggers or in application logic).  
   - E.g., if an IRO is updated, an “UPDATE” entry with the old and new values is written to `audit_trail`.  
4. **Tenant Isolation**  
   - All tables carry a `tenant_id` (and possibly a separate schema, e.g., `tenant_abc.iro`).  
   - Use either **schema-based** or **RLS-based** approach to ensure that queries by Tenant A cannot see Tenant B’s rows.

---

#### 7. Additional Implementation Tips

1. **Foreign Keys & CASCADE/RESTRICT**  
   - Decide carefully whether to cascade deletes on main entities like `IRO`. For heavily regulated data, you may prefer **RESTRICT** so no data is inadvertently removed.  
   - Alternatively, “soft delete” an IRO with a status flag, preserving the data and references until an official archival.  

2. **Data Retention & Archiving**  
   - Some compliance regimes (GDPR, SOC 2) require that data be retained for a specific period.  
   - Plan for data archiving or partitioning older records to avoid indefinite DB growth.  

3. **Row-Level Security (RLS) Policies** (If you choose the single-schema approach)  
   ```sql
   ALTER TABLE tenant_xyz.iro ENABLE ROW LEVEL SECURITY;
   CREATE POLICY iro_tenant_policy ON tenant_xyz.iro
   FOR ALL
   TO saas_app_role
   USING (tenant_id = current_setting('app.current_tenant_id')::int);
   ```
   - Replicate similar policies for `dm_assessment`, `review`, `signoff`, and `audit_trail`.  

4. **Schema-Based Isolation**  
   - If each tenant is mapped to its own schema, replicate the table definitions per schema (`tenant_abc.iro`, `tenant_abc.dm_assessment`, etc.).  
   - More straightforward to manage for small or moderate scale but can become cumbersome if you have hundreds or thousands of tenants.  

5. **Triggers for Audit Logging**  
   - You can use **PostgreSQL triggers** to automatically insert into `audit_trail` on `INSERT/UPDATE/DELETE`.  
   - Alternatively, the application layer can handle these writes (more control over the structure of `data_diff`).

---

#### 8. Pitfalls to Avoid

1. **Over-Indexing**  
   - Each new index adds overhead to writes. Start with essential indexes (tenant ID, foreign keys, commonly used filters) and add others if usage patterns justify them.  
2. **Unbounded JSON Growth**  
   - Large, arbitrary JSON fields can degrade performance if not managed. Regularly prune old keys or move large historical data to S3 for archival.  
3. **Complex RLS Policies**  
   - RLS can introduce queries that are harder to debug if you have multiple policies stacked. Thoroughly test them.  
4. **Cascading Deletes**  
   - Ensure you understand the cascade chain, especially for `iro`, `review`, `signoff`, and `dm_assessment` references. Inadvertent deletes can lead to data loss.  
5. **Insufficient Auditing**  
   - Failing to log crucial event details (e.g., who made the change, what data changed) can undermine compliance.  
6. **Missing Multi-Tenant Strategy**  
   - Not having a consistent approach (RLS vs. separate schemas) leads to confusion and potential data leaks. Commit to one approach or a well-documented hybrid tactic.

---

#### 9. Summary

Each of these **five core tables**—**IRO**, **DMAssessment**, **Review**, **Signoff**, and **AuditTrail**—plays a distinct role in **multi-tenant** Double Materiality workflows. Together, they provide:

- *Clear Ownership & Tracking* (IRO baseline).  
- *Materiality Evaluations* (DMAssessment).  
- *Formal Review Processes & Approvals* (Review & Signoff).  
- *Full Visibility & Compliance Trails* (AuditTrail).  

Following the **best practices** outlined here ensures a **secure**, **scalable**, and **compliant** data layer that meets **AWS Well-Architected Framework** pillars, **GDPR/SOC2** requirements, and the functional needs of an **Enterprise SaaS**. 





---

## 2. SECURITY IMPLEMENTATION
### 2.1 Row-Level Security Policies
If you opt for **RLS** in a single schema:
```sql
-- Enable RLS at the table level:
ALTER TABLE iro ENABLE ROW LEVEL SECURITY;

-- Define a POLICY that ensures a user only sees rows matching their tenant_id
CREATE POLICY iro_tenant_policy ON iro
FOR SELECT
TO saas_app_role  -- The DB role used by the application
USING (tenant_id = current_setting('app.current_tenant_id')::int);

-- Similar policies for INSERT, UPDATE, DELETE with appropriate checks
```
- Application sets the `current_setting('app.current_tenant_id')` parameter or uses a session variable so the DB can apply RLS automatically.

### 2.2 Encryption Configuration
- **Data at Rest**: AWS KMS-based encryption on RDS side, plus `sslmode=verify-full` for connections.  
- **Data in Transit**: Enforce TLS 1.2 or higher for all client connections.  
- **Secrets Management**: **AWS Secrets Manager** or SSM Parameter Store for database credentials, rotated regularly.

### 2.3 Access Controls
1. **AWS IAM**  
   - Grant the **minimum set of privileges** to microservices (e.g., read/write to specific S3 buckets, retrieve DB credentials).  
2. **DB Roles**  
   - **Application Role** used by app containers (limited DDL rights, strictly DML read/write).  
   - **Admin Role** restricted to DB maintenance tasks (schema changes, updates).  
3. **Network Security**  
   - Place RDS instances in **private subnets** with no public IP.  
   - Use **Security Groups** to allow traffic only from the application tasks in AWS Fargate/ECS.  
4. **WAF & Shield**  
   - **AWS WAF** filters SQL injection, XSS, malicious IPs.  
   - **AWS Shield Standard** default; upgrade to Advanced if you observe persistent DDoS attempts.

---

## 3. PROVISIONING AUTOMATION
### 3.1 Infrastructure as Code Snippets
Use **AWS CloudFormation** or **Terraform**. Example snippet in **Terraform** (pseudo-code):

```hcl
resource "aws_rds_cluster" "tenant_db" {
  engine         = "aurora-postgresql"
  engine_version = "13"
  ...
  storage_encrypted = true
  kms_key_id        = aws_kms_key.db_encryption_key.arn
  master_username   = var.db_master_user
  master_password   = var.db_master_password

  # Multi-AZ, auto-scaling, ...
}

resource "aws_ecs_cluster" "saas_app_cluster" {
  name = "saas-app-cluster"
}

resource "aws_ecs_task_definition" "saas_app_td" {
  family                = "saas-app"
  network_mode          = "awsvpc"
  requires_compatibilities = ["FARGATE"]

  container_definitions = file("${path.module}/container_definitions.json")
  cpu                   = 512
  memory                = 1024
  execution_role_arn    = var.ecs_execution_role
}

resource "aws_ecs_service" "saas_app_service" {
  name            = "saas-app-service"
  cluster         = aws_ecs_cluster.saas_app_cluster.id
  task_definition = aws_ecs_task_definition.saas_app_td.arn
  desired_count   = 2
  network_configuration {
    subnets          = var.private_subnets
    security_groups  = [aws_security_group.app_sg.id]
    assign_public_ip = false
  }
  load_balancer {
    target_group_arn = aws_lb_target_group.saas_app_tg.arn
    container_name   = "saas-app"
    container_port   = 8080
  }
  depends_on = [aws_lb_listener.saas_app_listener]
}
```

### 3.2 Provisioning Workflow
1. **Tenant Signup** triggers a microservice event (via Amazon API Gateway or a serverless function).  
2. **Terraform/CloudFormation Pipeline** (or AWS CDK) runs automatically to:  
   - Create new **schema** (if using separate schemas).  
   - Execute any **custom initialization scripts** (create tables, set RLS or roles).  
   - Register tenant in a **tenant_config** table or external config store.  
3. **Validation** step ensures DB objects were created successfully.  
4. **Notification** is sent to the admin or the new tenant upon successful provisioning.

### 3.3 Error Handling
- Implement **idempotent** creation steps so if partial failures occur, the pipeline can retry without duplicating resources.  
- Log every step (CloudWatch logs) to track environment initialization.  
- Use **SNS** or a Slack webhook for immediate notifications about provisioning failures or partial successes.

---

## 4. COMPLIANCE MEASURES
### 4.1 Audit Logging
- **Database Layer**:  
  - Enable **PostgreSQL logs** for queries and combine them with row-level `AuditTrail` table for user-driven actions.  
  - Store logs in **CloudWatch** or **Amazon S3** (versioned for immutability).  
- **Application Layer**:  
  - Capture each create, update, delete event in the `audit_trail` table (fields: `tenant_id`, `entity_type`, `action`, `timestamp`, `data_diff`).  
  - Maintain **14+ days** of logs in easy-to-access storage; archive older logs to Glacier.

### 4.2 Data Protection
- **GDPR**  
  - Provide a “right to erasure” process: a function that either anonymizes or removes user PII.  
  - Document data flows and ensure data is processed only for the purposes stated.  
- **SOC 2**  
  - Implement consistent control frameworks for **confidentiality, integrity, availability** (e.g., restricting DB access, logging all admin actions).  
  - Evidence logs (change management, access control reviews) must be easily retrievable.

### 4.3 Compliance Validations
- **Penetration Testing**: Periodic tests on the multi-tenant environment to check for cross-tenant data leaks.  
- **Encryption at Rest & in Transit**: Confirm TLS 1.2 or 1.3 is enforced, AWS KMS is active for RDS encryption.  
- **Incident Response**: Define runbooks for data breaches, unauthorized access, or system downtime compliance notifications.

---

## 5. CODE EXAMPLES
### 5.1 SQL Creation Scripts (Schema-Based)
```sql
-- Example creation in a dedicated schema approach:
CREATE SCHEMA IF NOT EXISTS tenant_123 AUTHORIZATION db_admin;

CREATE TABLE tenant_123.iro (
    iro_id SERIAL PRIMARY KEY,
    tenant_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    created_on TIMESTAMP DEFAULT NOW()
);

CREATE TABLE tenant_123.audit_trail (
    audit_id SERIAL PRIMARY KEY,
    tenant_id INT NOT NULL,
    entity_type VARCHAR(50),
    entity_id INT,
    action VARCHAR(50),
    user_id INT,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    data_diff JSONB
);

-- And so on for custom domain tables like DMAssessment, Review, Signoff, etc.
```

### 5.2 Security Policy Definitions (Row-Level Security)
```sql
-- Enable RLS on a shared table
ALTER TABLE public.iro ENABLE ROW LEVEL SECURITY;

-- Example policy to allow SELECT only for rows matching the session’s tenant_id:
CREATE POLICY iro_select_policy ON public.iro
FOR SELECT
TO saas_app_role
USING (tenant_id = current_setting('app.current_tenant_id')::int);

-- Additional policies for INSERT, UPDATE, DELETE as needed
```

### 5.3 Provisioning Scripts (Sample AWS CLI / Bash)
```bash
#!/usr/bin/env bash
# Creates a new tenant schema and user in PostgreSQL

TENANT_NAME=$1
DB_ENDPOINT=$2
DB_ADMIN_USER=$3
DB_ADMIN_PASS=$4

psql "host=$DB_ENDPOINT user=$DB_ADMIN_USER password=$DB_ADMIN_PASS dbname=postgres" <<SQL
    CREATE SCHEMA IF NOT EXISTS tenant_$TENANT_NAME;
    -- Optionally create a role for the tenant
    CREATE ROLE tenant_role_$TENANT_NAME LOGIN PASSWORD 'generateStrongPasswordHere';
    GRANT USAGE ON SCHEMA tenant_$TENANT_NAME TO tenant_role_$TENANT_NAME;
    GRANT CREATE ON SCHEMA tenant_$TENANT_NAME TO tenant_role_$TENANT_NAME;

    -- Create the necessary tables in tenant schema
    CREATE TABLE tenant_$TENANT_NAME.iro (...);
    CREATE TABLE tenant_$TENANT_NAME.dm_assessment (...);
    CREATE TABLE tenant_$TENANT_NAME.audit_trail (...);

    -- More table definitions or function creation as needed.
SQL

if [ $? -eq 0 ]; then
    echo "Tenant $TENANT_NAME provisioned successfully."
else
    echo "Error: Tenant $TENANT_NAME provisioning failed."
    exit 1
fi
```

---

### Final Remarks

This **production-ready multi-tenant architecture** on **AWS PostgreSQL** balances **secure tenant isolation**, **scalability**, and **compliance**. By leveraging **schema-based** or **RLS** isolation patterns, **end-to-end encryption**, and **automated provisioning** workflows, the design satisfies **GDPR** and **SOC2** requirements while offering a streamlined path to onboarding new tenants. Leveraging **AWS native services** (e.g., CloudFormation/Terraform, Secrets Manager, GuardDuty) helps ensure operational excellence and fosters a robust DevSecOps culture. 