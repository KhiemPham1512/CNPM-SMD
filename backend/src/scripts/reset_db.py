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
from dotenv import load_dotenv

# Bootstrap: ensure backend/src is in sys.path
_script_dir = Path(__file__).resolve().parent
_src_dir = _script_dir.parent
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

# Load .env file from backend/ directory (project root)
# This ensures DATABASE_URI is loaded before Config is used
_env_path = _src_dir.parent / ".env"  # backend/.env
load_dotenv(dotenv_path=_env_path if _env_path.exists() else None)

from infrastructure.databases.base import Base
from config import Config

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.engine import make_url  # ✅ FIX: robust URL parsing

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


def _ensure_str(value):
    """Ensure the given value is str (decode bytes/bytearray)."""
    if isinstance(value, (bytes, bytearray)):
        return value.decode("utf-8")
    return value


def extract_database_name(database_uri):
    """Extract database name from SQLAlchemy connection URI."""
    database_uri = _ensure_str(database_uri)
    url = make_url(database_uri)
    return url.database or "smd"


def get_master_engine(database_uri):
    """Create engine connected to master database (MSSQL)."""
    database_uri = _ensure_str(database_uri)

    # ✅ FIX: Do NOT build URI manually with urlparse/urlunparse.
    # Use SQLAlchemy URL object to avoid broken URLs due to special chars, params, etc.
    url = make_url(database_uri)
    master_url = url.set(database="master")

    return create_engine(master_url)


def terminate_database_connections(master_engine, db_name):
    """Terminate all active connections to the target database."""
    print(f"  Terminating active connections to database '{db_name}'...")

    try:
        with master_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            sql = text(f"ALTER DATABASE [{db_name}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE")
            conn.execute(sql)
        print("  ✓ Set database to SINGLE_USER mode (terminated connections)")
    except ProgrammingError as e:
        if "Cannot open database" in str(e) or "does not exist" in str(e):
            print(f"  ⚠ Database '{db_name}' does not exist (will be created)")
            return
        print(f"  ⚠ Could not terminate connections: {str(e)[:150]}")
    except Exception as e:
        print(f"  ⚠ Error terminating connections: {str(e)[:150]}")


def drop_and_recreate_database(master_engine, db_name):
    """Drop and recreate the database."""
    try:
        terminate_database_connections(master_engine, db_name)

        print(f"  Dropping database '{db_name}'...")
        try:
            with master_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
                drop_sql = text(f"DROP DATABASE IF EXISTS [{db_name}]")
                conn.execute(drop_sql)
            print(f"  ✓ Dropped database '{db_name}'")
        except Exception as e:
            print(f"  ⚠ Could not drop database (may not exist): {str(e)[:150]}")

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
            table_names = inspector.get_table_names()

            print("  Disabling all foreign key constraints...")
            for table_name in table_names:
                fks = inspector.get_foreign_keys(table_name)
                for fk in fks:
                    constraint_name = fk.get("name")
                    if not constraint_name:
                        continue
                    safe_table = table_name.replace("]", "]]")
                    safe_constraint = constraint_name.replace("]", "]]")
                    try:
                        disable_sql = text(
                            f"ALTER TABLE [{safe_table}] NOCHECK CONSTRAINT [{safe_constraint}]"
                        )
                        conn.execute(disable_sql)
                        fk_count += 1
                    except Exception:
                        pass

            print(f"  ✓ Disabled {fk_count} foreign key constraint(s)")

            print("  Dropping tables...")
            for table_name in table_names:
                safe_table = table_name.replace("]", "]]")
                try:
                    drop_sql = text(f"DROP TABLE IF EXISTS [{safe_table}]")
                    conn.execute(drop_sql)
                    table_count += 1
                    print(f"    ✓ Dropped [{safe_table}]")
                except Exception as e:
                    print(f"    ⚠ Could not drop table [{safe_table}]: {str(e)[:150]}")

            print(f"  ✓ Dropped {table_count} table(s)")
            return True

    except Exception as e:
        print(f"  ✗ Error in fallback method: {str(e)[:200]}")
        return False


def reset_database():
    print("=" * 60)
    print("SMD Database Reset Script")
    print("=" * 60)
    print()
    print("WARNING: This will DELETE ALL DATA in the database!")
    print()

    response = input("Are you sure you want to reset the database? (yes/no): ")
    if response.lower() != "yes":
        print("Reset cancelled.")
        return

    print()

    # Guard: Check if DATABASE_URI is configured
    database_uri = Config.DATABASE_URI
    if not database_uri:
        raise ValueError(
            "DATABASE_URI is not set. Please:\n"
            "  1. Create a .env file in the backend/ directory\n"
            "  2. Add DATABASE_URI=mssql+pymssql://sa:Aa%40123456@127.0.0.1:1433/smd\n"
            "  3. Or set DATABASE_URI as an environment variable\n"
            "\n"
            "Example .env location: backend/.env"
        )
    
    db_name = extract_database_name(database_uri)
    print(f"Target database: '{db_name}'")
    print()

    print("Step 1: Attempting to drop and recreate database...")
    master_engine = get_master_engine(database_uri)
    db_dropped = drop_and_recreate_database(master_engine, db_name)

    if not db_dropped:
        print()
        print("Step 1 (Fallback): Dropping tables individually...")
        # Create app engine for fallback operations
        app_engine = create_engine(database_uri)
        inspector = inspect(app_engine)
        success = disable_constraints_and_drop_tables(app_engine, inspector)
        if not success:
            print("  ✗ Fallback method also failed. Please check database permissions.")
            raise Exception("Failed to reset database")

    print()

    print("Step 2: Creating all tables from models...")
    try:
        # Create app engine for table creation
        app_engine = create_engine(database_uri)
        Base.metadata.create_all(bind=app_engine)
        inspector = inspect(app_engine)
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


if __name__ == "__main__":
    reset_database()
