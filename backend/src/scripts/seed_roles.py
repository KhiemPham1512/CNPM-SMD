"""
Seed script to create standard roles and a principal user for SMD system.

Roles created (exactly 6 roles):
- ADMIN (System Administrator)
- LECTURER (Lecturer/Teacher)
- HOD (Head of Department)
- AA (Academic Affairs)
- PRINCIPAL (Final Approver / Strategic Flow)
- STUDENT (Student)

Usage:
    python -m scripts.seed_roles
    or
    python scripts/seed_roles.py
"""
import sys
from pathlib import Path
# Bootstrap: ensure backend/src is in sys.path
_script_dir = Path(__file__).resolve().parent
_src_dir = _script_dir.parent
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

from infrastructure.databases.mssql import SessionLocal, engine
from infrastructure.databases.base import Base
from infrastructure.models.role import Role
from infrastructure.models.user import User
from infrastructure.models.user_role import UserRole
from werkzeug.security import generate_password_hash
from datetime import datetime

# Standardized role names - exactly 6 roles: ADMIN, LECTURER, HOD, AA, PRINCIPAL, STUDENT
ROLES = ['ADMIN', 'LECTURER', 'HOD', 'AA', 'PRINCIPAL', 'STUDENT']


def seed_roles():
    """Create all standard roles if they don't exist. Upsert logic: update name if exists."""
    db = SessionLocal()
    try:
        for role_name in ROLES:
            existing_role = db.query(Role).filter_by(role_name=role_name).first()
            if not existing_role:
                role = Role(role_name=role_name)
                db.add(role)
                print(f"Created role: {role_name}")
            else:
                # Update role name if different (defensive - should not happen)
                if existing_role.role_name != role_name:
                    existing_role.role_name = role_name
                    print(f"Updated role name: {role_name}")
                else:
                    print(f"Role already exists: {role_name}")
        
        db.commit()
        print(f"Roles seeded successfully: {len(ROLES)} roles ({', '.join(ROLES)})")
    except Exception as e:
        db.rollback()
        print(f"Error seeding roles: {e}")
        raise
    finally:
        db.close()


def seed_principal_user():
    """Create a principal user with PRINCIPAL role."""
    db = SessionLocal()
    try:
        # Check if principal user already exists
        principal_user = db.query(User).filter_by(username='principal').first()
        if principal_user:
            print("Principal user already exists")
            return principal_user.user_id
        
        # Get PRINCIPAL role
        principal_role = db.query(Role).filter_by(role_name='PRINCIPAL').first()
        if not principal_role:
            raise ValueError("PRINCIPAL role not found. Run seed_roles() first.")
        
        # Create principal user
        principal_user = User(
            username='principal',
            password_hash=generate_password_hash('principal123'),  # Change in production!
            full_name='Principal User',
            email='principal@university.edu',
            status='active',
            created_at=datetime.utcnow()
        )
        db.add(principal_user)
        db.flush()  # Get user_id
        
        # Assign PRINCIPAL role
        user_role = UserRole(
            user_id=principal_user.user_id,
            role_id=principal_role.role_id
        )
        db.add(user_role)
        
        db.commit()
        print(f"Created principal user: {principal_user.username} (ID: {principal_user.user_id})")
        return principal_user.user_id
    except Exception as e:
        db.rollback()
        print(f"Error seeding principal user: {e}")
        raise
    finally:
        db.close()


def seed_all():
    """Seed roles and principal user."""
    print("Starting database seeding...")
    print("=" * 50)
    
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    print("Database tables verified/created")
    print("-" * 50)
    
    # Seed roles
    seed_roles()
    print("-" * 50)
    
    # Seed principal user
    seed_principal_user()
    print("-" * 50)
    
    print("=" * 50)
    print("Database seeding completed successfully!")


if __name__ == '__main__':
    seed_all()

