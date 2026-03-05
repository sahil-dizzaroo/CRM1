"""
Simplified script to sync tables from local PostgreSQL to Neon PostgreSQL.
This version does NOT require pg_dump – it uses SQL introspection only.

Usage:
1. Set environment variables:
   export LOCAL_DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/dbname"
   export NEON_DATABASE_URL="postgresql+asyncpg://user:pass@neon-host/dbname"

2. Run the script:
   python sync_tables_to_neon_simple.py
"""
import asyncio
import sys
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from urllib.parse import urlparse, quote_plus, unquote

# Import DDL generation function from the other script
import importlib.util
import pathlib

# Load get_table_ddl_async from sync_tables_to_neon.py
spec = importlib.util.spec_from_file_location(
    "sync_tables_to_neon_module",
    pathlib.Path(__file__).parent / "sync_tables_to_neon.py"
)
sync_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync_module)
get_table_ddl_async = sync_module.get_table_ddl_async


def parse_db_url(url: str) -> dict:
    """Parse database URL into components."""
    # Handle asyncpg URL format
    url_clean = url.replace("postgresql+asyncpg://", "postgresql://")
    parsed = urlparse(url_clean)
    
    hostname = parsed.hostname
    # Convert Docker container name "postgres" to "localhost" for pg_dump
    if hostname == "postgres":
        hostname = "localhost"
    
    return {
        "host": hostname,
        "port": parsed.port or 5432,
        "user": parsed.username,
        "password": parsed.password,
        "database": parsed.path[1:] if parsed.path.startswith("/") else parsed.path,
    }


async def get_table_list_local(session: AsyncSession) -> list:
    """Get list of all tables in the database (local helper to avoid re-export changes)."""
    query = text(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_type = 'BASE TABLE'
        ORDER BY table_name
        """
    )
    result = await session.execute(query)
    return [row[0] for row in result.fetchall()]


def extract_table_ddl_from_dump(dump_content: str, table_name: str) -> str:
    """Extract CREATE TABLE statement for a specific table from pg_dump output."""
    lines = dump_content.split('\n')
    create_lines = []
    in_table = False
    brace_count = 0
    
    for line in lines:
        # Look for CREATE TABLE statement for our table
        if f'CREATE TABLE public.{table_name}' in line or f'CREATE TABLE {table_name}' in line:
            in_table = True
            create_lines.append(line)
            # Count opening braces
            brace_count = line.count('(') - line.count(')')
            continue
        
        if in_table:
            create_lines.append(line)
            brace_count += line.count('(') - line.count(')')
            
            # If we've closed all braces and hit a semicolon, we're done
            if brace_count == 0 and ';' in line:
                break
    
    return '\n'.join(create_lines)


async def sync_tables():
    """Main function to sync tables from local to Neon."""
    print("=" * 70)
    print("Database Table Synchronization: Local → Neon")
    print("=" * 70)
    print()
    
    # Get connection strings (check LOCAL_DATABASE_URL first, fallback to DATABASE_URL)
    local_db_url = os.getenv("LOCAL_DATABASE_URL") or os.getenv("DATABASE_URL")
    neon_db_url = os.getenv("NEON_DATABASE_URL")
    
    if not local_db_url:
        print("❌ ERROR: LOCAL_DATABASE_URL or DATABASE_URL environment variable not set")
        print("   Example: postgresql+asyncpg://user:pass@localhost:5432/dbname")
        sys.exit(1)
    
    if not neon_db_url:
        print("❌ ERROR: NEON_DATABASE_URL environment variable not set")
        print("   Example: postgresql+asyncpg://user:pass@neon-host/dbname")
        print("\n💡 Set it with: set NEON_DATABASE_URL=your-neon-connection-string")
        sys.exit(1)
    
    # Clean URLs - strip quotes and whitespace that might have been added
    local_db_url = local_db_url.strip().strip('"').strip("'")
    neon_db_url = neon_db_url.strip().strip('"').strip("'")
    
    # Validate and clean URLs - ensure they're properly formatted
    # Check if URLs need encoding (passwords with special chars)
    try:
        # Test parse to see if URL is valid
        test_parse = urlparse(neon_db_url.replace("postgresql+asyncpg://", "postgresql://"))
        if not test_parse.hostname:
            raise ValueError("Could not parse hostname from Neon URL")
        # Check for empty labels in hostname (double dots, etc.)
        if '..' in test_parse.hostname or test_parse.hostname.startswith('.') or test_parse.hostname.endswith('.'):
            raise ValueError(f"Invalid hostname format: {test_parse.hostname}")
    except Exception as e:
        print(f"❌ ERROR: Invalid Neon database URL format: {e}")
        print(f"   Parsed hostname: {test_parse.hostname if 'test_parse' in locals() else 'N/A'}")
        print("   Make sure the URL is properly formatted")
        print("   Example: postgresql+asyncpg://user:password@host:port/dbname?ssl=require")
        print("\n💡 Tip: In Windows CMD, if your URL has special chars, use quotes:")
        print('   set NEON_DATABASE_URL="postgresql+asyncpg://user:pass@host/dbname"')
        sys.exit(1)
    
    # Show which env var was used
    if os.getenv("LOCAL_DATABASE_URL"):
        print("ℹ️  Using LOCAL_DATABASE_URL for local database")
    else:
        print("ℹ️  Using DATABASE_URL for local database")
    print()
    
    # Debug: Show parsed info (mask password)
    try:
        local_info = parse_db_url(local_db_url)
        neon_info = parse_db_url(neon_db_url)
        
        print(f"📊 Local Database: {local_info['database']}@{local_info['host']}:{local_info['port']}")
        print(f"☁️  Neon Database: {neon_info['database']}@{neon_info['host']}:{neon_info['port']}")
        
        # Check if hostname looks valid
        if not neon_info['host'] or '.' not in neon_info['host']:
            print(f"\n⚠️  WARNING: Neon hostname looks invalid: '{neon_info['host']}'")
            print("   This might cause connection issues.")
        print()
    except Exception as e:
        print(f"❌ ERROR parsing database URLs: {e}")
        print("   Check that your URLs are properly formatted")
        sys.exit(1)
    
    # Create engines for table comparison and DDL generation
    # Ensure URLs are properly formatted (handle query parameters correctly)
    # SQLAlchemy should handle query params, but let's make sure the URL is clean
    local_engine = create_async_engine(local_db_url, echo=False, connect_args={})
    # For Neon, ensure SSL is handled properly via query params in URL
    neon_engine = create_async_engine(neon_db_url, echo=False, connect_args={})
    
    local_session_maker = async_sessionmaker(local_engine, class_=AsyncSession, expire_on_commit=False)
    neon_session_maker = async_sessionmaker(neon_engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        # Get table lists
        print("🔍 Comparing table lists...")
        async with local_session_maker() as local_session:
            local_tables = await get_table_list_local(local_session)

        # For Neon we can reuse the same helper
        async with neon_session_maker() as neon_session:
            neon_tables = await get_table_list_local(neon_session)
        
        print(f"   Local database has {len(local_tables)} tables")
        print(f"   Neon database has {len(neon_tables)} tables")
        print()
        
        # Find missing tables
        missing_tables = [t for t in local_tables if t not in neon_tables]
        
        if not missing_tables:
            print("✅ All tables already exist in Neon database!")
            return
        
        print(f"📋 Found {len(missing_tables)} missing tables:")
        for table in missing_tables:
            print(f"   - {table}")
        print()

        # Create missing tables in Neon using SQL-based DDL generation
        print("🔨 Creating missing tables in Neon...")
        print()
        
        created_count = 0
        failed_tables = []
        
        for table_name in missing_tables:
            try:
                print(f"   Creating table '{table_name}'...", end=" ")
                
                # Get DDL for this table from local database using SQL introspection
                async with local_session_maker() as local_session:
                    table_ddl = await get_table_ddl_async(local_session, table_name)
                
                if not table_ddl:
                    print(f"❌ Could not generate DDL")
                    failed_tables.append(table_name)
                    continue
                
                # Execute CREATE TABLE on Neon
                async with neon_session_maker() as neon_session:
                    # Remove trailing semicolon if present
                    ddl_clean = table_ddl.strip().rstrip(';')
                    await neon_session.execute(text(ddl_clean))
                    await neon_session.commit()
                
                print("✅")
                created_count += 1
                
            except Exception as e:
                print(f"❌ Error: {str(e)[:100]}")
                failed_tables.append(table_name)
                async with neon_session_maker() as neon_session:
                    await neon_session.rollback()
        
        print()
        print("=" * 70)
        if created_count > 0:
            print(f"✅ Successfully created {created_count} table(s)")
        if failed_tables:
            print(f"❌ Failed to create {len(failed_tables)} table(s): {', '.join(failed_tables)}")
            print("\n💡 Tip: You may need to create these tables manually or check for dependencies")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await local_engine.dispose()
        await neon_engine.dispose()


if __name__ == "__main__":
    try:
        asyncio.run(sync_tables())
    except KeyboardInterrupt:
        print("\n\n⚠️  Synchronization interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
