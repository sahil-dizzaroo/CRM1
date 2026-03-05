# Database Synchronization Guide

This guide explains how to sync tables from your local PostgreSQL database to your Neon PostgreSQL database.

## Prerequisites

1. **PostgreSQL Client Tools**: You need `pg_dump` installed on your system
   - **Windows**: Install PostgreSQL from https://www.postgresql.org/download/windows/
   - **macOS**: `brew install postgresql`
   - **Linux**: `sudo apt-get install postgresql-client` (Debian/Ubuntu) or `sudo yum install postgresql` (RHEL/CentOS)

2. **Python Dependencies**: Make sure you have the required packages installed
   ```bash
   pip install sqlalchemy asyncpg
   ```

3. **Database Connection Strings**: You need connection strings for both databases

## Setup

### Step 1: Set Environment Variables

Set the following environment variables with your database connection strings:

**Windows (Command Prompt):**
```cmd
set LOCAL_DATABASE_URL=postgresql+asyncpg://crm_user:crm_pass@localhost:5432/crm_db
set NEON_DATABASE_URL=postgresql+asyncpg://user:password@your-neon-host.neon.tech/dbname
```

**Windows (PowerShell):**
```powershell
$env:LOCAL_DATABASE_URL="postgresql+asyncpg://crm_user:crm_pass@localhost:5432/crm_db"
$env:NEON_DATABASE_URL="postgresql+asyncpg://user:password@your-neon-host.neon.tech/dbname"
```

**Linux/macOS:**
```bash
export LOCAL_DATABASE_URL="postgresql+asyncpg://crm_user:crm_pass@localhost:5432/crm_db"
export NEON_DATABASE_URL="postgresql+asyncpg://user:password@your-neon-host.neon.tech/dbname"
```

### Step 2: Get Your Neon Connection String

1. Log in to your Neon dashboard
2. Select your project
3. Go to the "Connection Details" section
4. Copy the connection string (it will look like: `postgresql://user:password@host/dbname`)
5. Convert it to asyncpg format: `postgresql+asyncpg://user:password@host/dbname`

## Running the Sync Script

### Option 1: Simple Script (Recommended)

The simple script uses `pg_dump` to extract the exact schema:

```bash
cd Backend-CRM
python sync_tables_to_neon_simple.py
```

### Option 2: Advanced Script

The advanced script has a fallback method if `pg_dump` is not available:

```bash
cd Backend-CRM
python sync_tables_to_neon.py
```

## What the Script Does

1. **Connects** to both local and Neon databases
2. **Compares** the list of tables in both databases
3. **Identifies** tables that exist locally but not in Neon
4. **Extracts** the table definitions (DDL) from the local database
5. **Creates** the missing tables in Neon with the same structure

## Example Output

```
======================================================================
Database Table Synchronization: Local → Neon
======================================================================

📊 Local Database: crm_db@localhost:5432
☁️  Neon Database: dbname@your-neon-host.neon.tech:5432

✅ pg_dump found
🔍 Comparing table lists...
   Local database has 25 tables
   Neon database has 20 tables

📋 Found 5 missing tables:
   - site_workflow_steps
   - site_statuses
   - site_status_history
   - feasibility_requests
   - feasibility_responses

📥 Extracting schema from local database...
✅ Schema extracted successfully

🔨 Creating missing tables in Neon...

   Creating table 'site_workflow_steps'... ✅
   Creating table 'site_statuses'... ✅
   Creating table 'site_status_history'... ✅
   Creating table 'feasibility_requests'... ✅
   Creating table 'feasibility_responses'... ✅

======================================================================
✅ Successfully created 5 table(s)
======================================================================
```

## Troubleshooting

### Error: "pg_dump not found"
- Install PostgreSQL client tools (see Prerequisites)
- Make sure `pg_dump` is in your system PATH

### Error: "connection refused" or "authentication failed"
- Check your connection strings are correct
- Verify database credentials
- Ensure your local database is running
- Check if Neon database is accessible from your network

### Error: "relation already exists"
- Some tables might already exist in Neon
- The script will skip existing tables automatically

### Error: "foreign key constraint" or "dependency" errors
- Some tables might have dependencies on other tables
- Try running the script multiple times (it will skip already-created tables)
- Or create tables manually in the correct order

### Tables created but missing indexes/constraints
- The script creates tables and basic constraints
- Some advanced indexes or constraints might need to be added manually
- Check the pg_dump output for any additional DDL statements

## Manual Alternative

If the script doesn't work, you can manually sync tables:

1. **Dump schema from local database:**
   ```bash
   pg_dump --schema-only --no-owner --no-privileges -h localhost -U crm_user -d crm_db > schema.sql
   ```

2. **Review and edit schema.sql** to keep only the tables you need

3. **Apply to Neon:**
   ```bash
   psql "your-neon-connection-string" < schema.sql
   ```

## Notes

- **Data is NOT copied**: This script only syncs table structures, not data
- **Indexes and constraints**: Basic indexes and constraints are included, but complex ones might need manual addition
- **Enums and custom types**: Custom PostgreSQL types (enums) should be created first if they don't exist in Neon
- **Foreign keys**: Foreign key constraints are created, but make sure referenced tables exist first

## Next Steps

After syncing tables:
1. Verify tables were created correctly in Neon
2. Check that indexes and constraints are in place
3. Test your application with the Neon database
4. Consider syncing data if needed (use `pg_dump --data-only`)
