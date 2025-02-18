<goal>
based on the "core table change request" below, please update the original core table design in the tenant schema architecture for a multi-tenant Enterprise SaaS solution on AWS PostgreSQL.
</goal>

<context>
You are a Senior Cloud Solutions Architect specializing in multi-tenant SaaS applications on AWS. You have extensive experience with PostgreSQL, data isolation patterns, and security compliance requirements (GDPR, SOC2).
</context>


<output_format>
Provide a COMPLETE UPDATED SCHEMA DESIGN in the following structured format:

1. SCHEMA DESIGN
   - Database structure
   - Isolation method
   - Naming conventions
   - Core tables

</output_format>

<constraints>
- Must follow AWS Well-Architected Framework
- Must be compliant with GDPR and SOC2
- Must support horizontal scaling
- Must enable tenant isolation
- Must include automated provisioning
</constraints>



<core table change request>

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

</core table change request>


<original design>

</original design>