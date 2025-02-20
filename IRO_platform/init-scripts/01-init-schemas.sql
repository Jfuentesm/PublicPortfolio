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