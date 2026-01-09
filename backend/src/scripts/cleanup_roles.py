"""
Cleanup script to remove invalid roles from the database.

This script removes roles that are NOT in the canonical list:
- ADMIN, LECTURER, HOD, AA, PRINCIPAL, STUDENT

The script preserves foreign key integrity by checking for dependencies
before deletion and warning if deletion is blocked.

Usage:
    python -m scripts.cleanup_roles
    or
    python scripts/cleanup_roles.py
"""
import sys
from pathlib import Path

# Bootstrap: ensure backend/src is in sys.path
_script_dir = Path(__file__).resolve().parent
_src_dir = _script_dir.parent
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

# Load environment variables from .env file
# Look for .env in backend/src or backend directory
from dotenv import load_dotenv
env_path = _src_dir / '.env'
if not env_path.exists():
    # Try parent directory (backend/)
    env_path = _src_dir.parent / '.env'
load_dotenv(dotenv_path=env_path if env_path.exists() else None)

from config import Config
from infrastructure.models.role import Role
from infrastructure.models.user_role import UserRole
from infrastructure.models.role_permission import RolePermission
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import sessionmaker

# Canonical role names - exactly 6 roles
CANONICAL_ROLES = ['ADMIN', 'LECTURER', 'HOD', 'AA', 'PRINCIPAL', 'STUDENT']


def cleanup_roles():
    """
    Remove roles that are not in the canonical list.
    
    Preserves FK integrity by checking for dependencies before deletion.
    Logs warnings if deletion is blocked by foreign key constraints.
    """
    # Initialize database connection (standalone script, no Flask app)
    database_uri = Config.DATABASE_URI
    if not database_uri:
        # Try to get from os.environ directly as fallback
        import os
        database_uri = os.environ.get('DATABASE_URI')
        if not database_uri:
            raise ValueError(
                "DATABASE_URI must be set in environment.\n"
                "Options:\n"
                "  1. Set DATABASE_URI in your .env file (in backend/ or backend/src/ directory)\n"
                "  2. Set DATABASE_URI as environment variable\n"
                f"     Current working directory: {os.getcwd()}\n"
                f"     Script directory: {_src_dir}"
            )
    
    # Create engine and session factory
    engine = create_engine(
        database_uri,
        connect_args={
            'timeout': 30,
            'login_timeout': 30,
        },
        pool_pre_ping=True,
        pool_recycle=3600,
        pool_timeout=30,
        echo=False
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    deleted_count = 0
    blocked_count = 0
    errors = []
    
    try:
        # Get all roles from database
        all_roles = db.query(Role).all()
        print(f"Found {len(all_roles)} roles in database")
        print("-" * 50)
        
        # Identify roles to delete (not in canonical list)
        roles_to_delete = []
        for role in all_roles:
            if role.role_name not in CANONICAL_ROLES:
                roles_to_delete.append(role)
        
        if not roles_to_delete:
            print("No invalid roles found. Database is clean.")
            return
        
        print(f"Found {len(roles_to_delete)} invalid role(s) to remove:")
        for role in roles_to_delete:
            print(f"  - {role.role_name} (ID: {role.role_id})")
        print("-" * 50)
        
        # Check for dependencies and attempt deletion
        for role in roles_to_delete:
            role_name = role.role_name
            role_id = role.role_id
            
            # Check for user_role dependencies
            user_role_count = db.query(UserRole).filter_by(role_id=role_id).count()
            
            # Check for role_permission dependencies
            role_permission_count = db.query(RolePermission).filter_by(role_id=role_id).count()
            
            if user_role_count > 0 or role_permission_count > 0:
                print(f"WARNING: Cannot delete role '{role_name}' (ID: {role_id}) - has dependencies:")
                if user_role_count > 0:
                    print(f"  - {user_role_count} user_role(s) reference this role")
                if role_permission_count > 0:
                    print(f"  - {role_permission_count} role_permission(s) reference this role")
                print(f"  Please remove dependencies manually before deleting this role.")
                blocked_count += 1
                errors.append({
                    'role_name': role_name,
                    'role_id': role_id,
                    'reason': f'FK constraint: {user_role_count} user_roles, {role_permission_count} role_permissions'
                })
                continue
            
            # Safe to delete - no dependencies
            try:
                db.delete(role)
                db.flush()  # Test if deletion succeeds
                deleted_count += 1
                print(f"Deleted role: {role_name} (ID: {role_id})")
            except IntegrityError as e:
                # Should not happen if we checked dependencies, but handle gracefully
                db.rollback()
                print(f"ERROR: Failed to delete role '{role_name}' (ID: {role_id}): {e}")
                blocked_count += 1
                errors.append({
                    'role_name': role_name,
                    'role_id': role_id,
                    'reason': f'IntegrityError: {str(e)}'
                })
            except Exception as e:
                db.rollback()
                print(f"ERROR: Unexpected error deleting role '{role_name}' (ID: {role_id}): {e}")
                errors.append({
                    'role_name': role_name,
                    'role_id': role_id,
                    'reason': f'Unexpected error: {str(e)}'
                })
        
        # Commit all successful deletions
        if deleted_count > 0:
            db.commit()
            print("-" * 50)
            print(f"Successfully deleted {deleted_count} role(s)")
        
        # Summary
        print("=" * 50)
        print("Cleanup Summary:")
        print(f"  - Deleted: {deleted_count} role(s)")
        print(f"  - Blocked (FK constraints): {blocked_count} role(s)")
        if errors:
            print(f"  - Errors: {len(errors)} role(s)")
            print("\nBlocked/Error Details:")
            for error in errors:
                print(f"  - {error['role_name']} (ID: {error['role_id']}): {error['reason']}")
        
        # Verify final state
        remaining_roles = db.query(Role).all()
        remaining_names = [r.role_name for r in remaining_roles]
        print(f"\nRemaining roles ({len(remaining_roles)}): {', '.join(sorted(remaining_names))}")
        
        # Check if all canonical roles exist
        missing_canonical = set(CANONICAL_ROLES) - set(remaining_names)
        if missing_canonical:
            print(f"\nWARNING: Missing canonical roles: {', '.join(sorted(missing_canonical))}")
            print("Run seed_roles.py to create missing roles.")
        else:
            print(f"\n✓ All {len(CANONICAL_ROLES)} canonical roles are present")
        
    except OperationalError as e:
        # Database connection error
        db.rollback()
        print(f"\n✗ DATABASE CONNECTION ERROR")
        print(f"Error: {str(e)}")
        print("\nPossible causes:")
        print("  1. Database server is not running")
        print("  2. Wrong DATABASE_URI in .env file")
        print("  3. Network/firewall blocking connection")
        print("\nTo fix:")
        print("  - Ensure database server is running")
        print("  - Check DATABASE_URI in your .env file")
        print("  - Verify database server is accessible")
        raise
    except Exception as e:
        # Other errors
        db.rollback()
        import traceback
        print(f"\n✗ FATAL ERROR during cleanup: {e}")
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == '__main__':
    print("=" * 50)
    print("Role Cleanup Script")
    print("=" * 50)
    print(f"Canonical roles: {', '.join(CANONICAL_ROLES)}")
    print("=" * 50)
    cleanup_roles()
    print("=" * 50)
    print("Cleanup completed!")
