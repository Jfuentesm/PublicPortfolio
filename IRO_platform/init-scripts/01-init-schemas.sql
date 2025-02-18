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