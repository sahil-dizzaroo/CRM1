-- =====================================================================
-- migration_sync_local_to_neon.sql
--
-- Purpose:
--   Incrementally sync Neon (production) PostgreSQL schema to match the
--   cleaned local schema for the `public` schema, using ONLY additive,
--   idempotent, and data-safe operations.
--
-- Safety guarantees:
--   - NO data is deleted or modified.
--   - NO tables or columns are dropped.
--   - NO column types are changed.
--   - All statements are safe to run multiple times.
--
-- High-level changes:
--   1. Ensure required enum types exist (and are populated).
--   2. Ensure site status tables exist:
--        - site_statuses
--        - site_status_history
--   3. Ensure site workflow & document tables exist:
--        - site_workflow_steps
--        - site_documents
--   4. Ensure user role assignment table exists:
--        - user_role_assignments
--   5. Add indexes and constraints that mirror local.
--
-- IMPORTANT:
--   - This file is intended to be run against NEON (prod).
--   - Local has already been cleaned and is the source of truth.
-- =====================================================================


-- ---------------------------------------------------------------------
-- 0. (Optional but safe) Ensure pgcrypto extension for gen_random_uuid()
--    This is additive; if the extension is already installed, nothing happens.
-- ---------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS "pgcrypto";


-- ---------------------------------------------------------------------
-- 1. Enum types required by site status / workflow / documents
--    These are additive: they only create missing types.
--    If a type already exists, CREATE TYPE IF NOT EXISTS does nothing.
-- ---------------------------------------------------------------------

-- 1.a Primary site status enum (used by site_statuses, site_status_history)
CREATE TYPE IF NOT EXISTS site_primary_status AS ENUM (
    'UNDER_EVALUATION',
    'STARTUP',
    'INITIATING',
    'INITIATED_NOT_RECRUITING',
    'RECRUITING',
    'ACTIVE_NOT_RECRUITING',
    'COMPLETED',
    'SUSPENDED',
    'TERMINATED',
    'WITHDRAWN',
    'CLOSED'
);

-- 1.b Workflow step name enum (used by site_workflow_steps)
CREATE TYPE IF NOT EXISTS workflow_step_name AS ENUM (
    'site_identification',
    'cda_execution',
    'feasibility',
    'site_selection_outcome'
);

-- 1.c Step status enum (used by site_workflow_steps)
CREATE TYPE IF NOT EXISTS step_status AS ENUM (
    'not_started',
    'in_progress',
    'completed',
    'locked'
);

-- 1.d Document category enum (used by site_documents)
CREATE TYPE IF NOT EXISTS document_category AS ENUM (
    'investigator_cv',
    'signed_cda',
    'cta',
    'irb_package',
    'feasibility_questionnaire',
    'feasibility_response',
    'onsite_visit_report',
    'site_visibility_report',
    'other'
);

-- 1.e Ensure UserRole enum (userrole) has all required values for assignments.
--     This is additive: it only adds missing values; existing data is untouched.
ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'cra';
ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'study_manager';
ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'medical_monitor';


-- ---------------------------------------------------------------------
-- 2. Site status tables (site_statuses, site_status_history)
--    Source: local DB & create_site_status_tables.py
--    These tables track the primary status per site and its history.
-- ---------------------------------------------------------------------

-- 2.a Current primary status per site
CREATE TABLE IF NOT EXISTS site_statuses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    site_id UUID NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
    current_status site_primary_status NOT NULL,
    previous_status site_primary_status,
    metadata JSONB DEFAULT '{}'::JSONB,
    effective_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_site_statuses_site UNIQUE (site_id)
);

-- Indexes to support efficient queries by site and status
CREATE INDEX IF NOT EXISTS ix_site_statuses_site_id
    ON site_statuses (site_id);

CREATE INDEX IF NOT EXISTS ix_site_statuses_current_status
    ON site_statuses (current_status);


-- 2.b Immutable audit trail of all site status transitions
CREATE TABLE IF NOT EXISTS site_status_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    site_id UUID NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
    status site_primary_status NOT NULL,
    previous_status site_primary_status,
    metadata JSONB DEFAULT '{}'::JSONB,
    changed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_site_status_history_site_id
    ON site_status_history (site_id);

CREATE INDEX IF NOT EXISTS ix_site_status_history_status
    ON site_status_history (status);

CREATE INDEX IF NOT EXISTS ix_site_status_history_changed_at
    ON site_status_history (changed_at DESC);

-- 2.c Add missing columns to site_status_history (if they don't exist)
--    These columns were added to the model but were missing from the initial migration
DO $$
BEGIN
    -- Add triggering_event column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'site_status_history' 
        AND column_name = 'triggering_event'
    ) THEN
        ALTER TABLE site_status_history 
        ADD COLUMN triggering_event VARCHAR(100);
    END IF;

    -- Add reason column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'site_status_history' 
        AND column_name = 'reason'
    ) THEN
        ALTER TABLE site_status_history 
        ADD COLUMN reason TEXT;
    END IF;
END $$;


-- ---------------------------------------------------------------------
-- 3. Site workflow & documents tables
--    Source: local DB & create_site_workflow_tables.py
-- ---------------------------------------------------------------------

-- 3.a site_workflow_steps – workflow step state per site
CREATE TABLE IF NOT EXISTS site_workflow_steps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    site_id UUID NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
    step_name workflow_step_name NOT NULL,
    status step_status NOT NULL DEFAULT 'not_started',
    step_data JSONB DEFAULT '{}'::JSONB,
    completed_at TIMESTAMPTZ,
    completed_by VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_site_workflow_step UNIQUE (site_id, step_name)
);

CREATE INDEX IF NOT EXISTS ix_site_workflow_steps_site_id
    ON site_workflow_steps (site_id);

CREATE INDEX IF NOT EXISTS ix_site_workflow_steps_step_name
    ON site_workflow_steps (step_name);

CREATE INDEX IF NOT EXISTS ix_site_workflow_steps_status
    ON site_workflow_steps (status);


-- 3.b site_documents – document storage per site (Site Master File)
CREATE TABLE IF NOT EXISTS site_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    site_id UUID NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
    category document_category NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    content_type VARCHAR(100) NOT NULL,
    size INTEGER NOT NULL,
    uploaded_by VARCHAR(255),
    uploaded_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    description TEXT,
    metadata JSONB DEFAULT '{}'::JSONB
);

CREATE INDEX IF NOT EXISTS ix_site_documents_site_id
    ON site_documents (site_id);

CREATE INDEX IF NOT EXISTS ix_site_documents_category
    ON site_documents (category);

CREATE INDEX IF NOT EXISTS ix_site_documents_uploaded_at
    ON site_documents (uploaded_at DESC);


-- ---------------------------------------------------------------------
-- 4. user_role_assignments table
--    Source: local DB & create_role_assignments_table.py
--    Purpose: link users to roles (CRA, Study Manager, Medical Monitor)
--             with specific site/study access.
-- ---------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS user_role_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    role userrole NOT NULL,
    site_id UUID,
    study_id UUID,
    assigned_by VARCHAR(255),
    assigned_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_user_role_user
        FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_user_role_site
        FOREIGN KEY (site_id)
        REFERENCES sites(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_user_role_study
        FOREIGN KEY (study_id)
        REFERENCES studies(id)
        ON DELETE CASCADE,

    CONSTRAINT chk_role_type CHECK (
        role IN ('cra', 'study_manager', 'medical_monitor')
    )
);

-- Indexes to support efficient permission queries
CREATE INDEX IF NOT EXISTS ix_user_role_assignments_user_id
    ON user_role_assignments (user_id);

CREATE INDEX IF NOT EXISTS ix_user_role_assignments_role
    ON user_role_assignments (role);

CREATE INDEX IF NOT EXISTS ix_user_role_assignments_site_id
    ON user_role_assignments (site_id);

CREATE INDEX IF NOT EXISTS ix_user_role_assignments_study_id
    ON user_role_assignments (study_id);

CREATE INDEX IF NOT EXISTS ix_user_role_assignments_user_role
    ON user_role_assignments (user_id, role);


-- ---------------------------------------------------------------------
-- 5. Read-only validation queries (safe to run after migration)
--    These do NOT change any data; they just let you verify schema.
-- ---------------------------------------------------------------------

-- Validate tables present in public schema
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;

-- Validate columns and data types
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'public'
ORDER BY table_name, ordinal_position;

