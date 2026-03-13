-- SQL script to create site_profiles table
-- Run this directly in your PostgreSQL database if the Python migration script has connection issues

CREATE TABLE IF NOT EXISTS site_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    site_id UUID NOT NULL UNIQUE,
    site_name VARCHAR(500),
    hospital_name VARCHAR(500),
    pi_name VARCHAR(255),
    pi_email VARCHAR(255),
    pi_phone VARCHAR(50),
    primary_contracting_entity VARCHAR(500),
    authorized_signatory_name VARCHAR(255),
    authorized_signatory_email VARCHAR(255),
    authorized_signatory_title VARCHAR(255),
    address_line_1 VARCHAR(500),
    city VARCHAR(255),
    state VARCHAR(255),
    country VARCHAR(255),
    postal_code VARCHAR(50),
    site_coordinator_name VARCHAR(255),
    site_coordinator_email VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_site_profile_site
        FOREIGN KEY(site_id) 
        REFERENCES sites(id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_site_profiles_site_id
    ON site_profiles (site_id);
