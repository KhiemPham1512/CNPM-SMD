"""
Database Reset Script for SMD Backend

This script drops and recreates the database for fast DEV reset.
Use this when you need to reset the database schema (e.g., after model changes).

WARNING: This will DELETE ALL DATA in the database!

Usage:
    python -m scripts.reset_db
    or
    python scripts/reset_db.py
"""
import sys
from pathlib import Path
# Bootstrap: ensure backend/src is in sys.path
_script_dir = Path(__file__).resolve().parent
_src_dir = _script_dir.parent
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

from infrastructure.databases.mssql import engine
from infrastructure.databases.base import Base
from config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import ProgrammingError
from urllib.parse import urlparse, urlunparse, parse_qs

# Import all models to ensure they're registered with Base.metadata
from infrastructure.models import (
    user, role, user_role, permission, role_permission,
    department, program, subject, subject_relation,
    syllabus, syllabus_version, syllabus_section,
    plo, clo, clo_plo_map, assessment_item,
    review_round, review_comment, workflow_action,
    notification, subscription, feedback,
    ai_job, ai_summary, system_setting, audit_log
)


def extract_database_name(database_uri):
    """Extract database name from SQLAlchemy connection URI."""
    # Parse the URI
    parsed = urlparse(database_uri)
    
    # Extract database name from path (e.g., /smd -> smd)
    db_name = parsed.path.lstrip('/')
    
    # If no database in path, try to extract from query params or use default
    if not db_name:
        # Try to get from query string
        query_params = parse_qs(parsed.query)
        if 'database' in query_params:
            db_name = query_params['database'][0]
        else:
            # Default fallback
            db_name = 'smd'
    
    return db_name


def get_master_engine(database_uri):
    """Create engine connected to master database."""
    # Parse the URI
    parsed = urlparse(database_uri)
    
    # Replace database name with 'master'
    master_path = '/master'
    master_uri = urlunparse((
        parsed.scheme,
        parsed.netloc,
        master_path,
        parsed.params,
        parsed.query,
        parsed.fragment
    ))
    
    return create_engine(master_uri)


def terminate_database_connections(master_engine, db_name):
    """Terminate all active connections to the target database."""
    print(f"  Terminating active connections to database '{db_name}'...")
    
    try:
        # Set database to single user mode (kills other connections)
        # Use AUTOCOMMIT for DDL operations
        with master_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            sql = text(f"ALTER DATABASE [{db_name}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE")
            conn.execute(sql)
        print(f"  ✓ Set database to SINGLE_USER mode (terminated connections)")
    except ProgrammingError as e:
        # Database might not exist yet, which is okay
        if "Cannot open database" in str(e) or "does not exist" in str(e):
            print(f"  ⚠ Database '{db_name}' does not exist (will be created)")
            return
        else:
            print(f"  ⚠ Could not terminate connections: {str(e)[:100]}")
    except Exception as e:
        print(f"  ⚠ Error terminating connections: {str(e)[:100]}")


def drop_and_recreate_database(master_engine, db_name):
    """Drop and recreate the database."""
    try:
        # Terminate connections first (separate operation)
        terminate_database_connections(master_engine, db_name)
        
        # Drop database - MUST use AUTOCOMMIT (MSSQL doesn't allow DROP DATABASE in transaction)
        print(f"  Dropping database '{db_name}'...")
        try:
            with master_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
                drop_sql = text(f"DROP DATABASE IF EXISTS [{db_name}]")
                conn.execute(drop_sql)
            print(f"  ✓ Dropped database '{db_name}'")
        except Exception as e:
            # If drop fails, database might not exist - continue to create
            print(f"  ⚠ Could not drop database (may not exist): {str(e)[:100]}")
        
        # Create database - MUST use AUTOCOMMIT (MSSQL doesn't allow CREATE DATABASE in transaction)
        print(f"  Creating database '{db_name}'...")
        with master_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            create_sql = text(f"CREATE DATABASE [{db_name}]")
            conn.execute(create_sql)
        print(f"  ✓ Created database '{db_name}'")
        
        return True
    except Exception as e:
        print(f"  ✗ Error dropping/recreating database: {str(e)[:200]}")
        return False


def disable_constraints_and_drop_tables(engine, inspector):
    """Fallback: Disable constraints and drop all tables using raw SQL."""
    print("  Using fallback method: disabling constraints and dropping tables...")
    
    table_count = 0
    fk_count = 0
    
    try:
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            
            # Get all tables
            table_names = inspector.get_table_names()
            
            # Disable all foreign key constraints using MSSQL-specific approach
            print("  Disabling all foreign key constraints...")
            for table_name in table_names:
                fks = inspector.get_foreign_keys(table_name)
                for fk in fks:
                    constraint_name = fk['name']
                    safe_table = table_name.replace(']', ']]')
                    safe_constraint = constraint_name.replace(']', ']]')
                    
                    try:
                        # Disable constraint check
                        disable_sql = text(f"ALTER TABLE [{safe_table}] NOCHECK CONSTRAINT [{safe_constraint}]")
                        conn.execute(disable_sql)
                        fk_count += 1
                    except Exception as e:
                        # Continue if constraint doesn't exist or already disabled
                        pass
            
            print(f"  ✓ Disabled {fk_count} foreign key constraint(s)")
            
            # Drop all tables one by one with progress
            print("  Dropping tables...")
            for table_name in table_names:
                safe_table = table_name.replace(']', ']]')
                try:
                    drop_sql = text(f"DROP TABLE IF EXISTS [{safe_table}]")
                    conn.execute(drop_sql)
                    table_count += 1
                    print(f"    ✓ Dropped [{safe_table}]")
                except Exception as e:
                    print(f"    ⚠ Could not drop table [{safe_table}]: {str(e)[:100]}")
            
            print(f"  ✓ Dropped {table_count} table(s)")
            return True
                
    except Exception as e:
        print(f"  ✗ Error in fallback method: {str(e)[:200]}")
        return False


def reset_database():
    """
    Drop and recreate database, or fallback to dropping tables.
    
    Strategy:
    1. Try to drop and recreate the entire database (fastest)
    2. If that fails, fallback to disabling constraints and dropping tables
    3. Then recreate all tables from Base.metadata
    """
    print("=" * 60)
    print("SMD Database Reset Script")
    print("=" * 60)
    print()
    print("WARNING: This will DELETE ALL DATA in the database!")
    print()
    
    # Confirm before proceeding
    response = input("Are you sure you want to reset the database? (yes/no): ")
    if response.lower() != 'yes':
        print("Reset cancelled.")
        return
    
    print()
    
    # Extract database name from URI
    database_uri = Config.DATABASE_URI
    db_name = extract_database_name(database_uri)
    print(f"Target database: '{db_name}'")
    print()
    
    # Try primary method: Drop and recreate database
    print("Step 1: Attempting to drop and recreate database...")
    master_engine = get_master_engine(database_uri)
    db_dropped = drop_and_recreate_database(master_engine, db_name)
    
    if not db_dropped:
        print()
        print("Step 1 (Fallback): Dropping tables individually...")
        # Fallback: Disable constraints and drop tables
        inspector = inspect(engine)
        success = disable_constraints_and_drop_tables(engine, inspector)
        if not success:
            print("  ✗ Fallback method also failed. Please check database permissions.")
            raise Exception("Failed to reset database")
    
    print()
    
    # Step 2: Create all tables
    print("Step 2: Creating all tables from models...")
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        # Count tables that were created
        inspector = inspect(engine)
        table_count = len(inspector.get_table_names())
        print(f"  ✓ Created {table_count} table(s)")
    except Exception as e:
        print(f"  ✗ Error creating tables: {e}")
        raise
    
    print()
    print("=" * 60)
    print("Database reset completed successfully!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. Run seed_roles.py to create standard roles")
    print("  2. Run seed_mvp.py to create test data")
    print()


if __name__ == '__main__':
    reset_database()
