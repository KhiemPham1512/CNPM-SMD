"""
MVP Database Seeding Script for SMD Workflow Testing

This script creates:
- Roles: ADMIN, LECTURER, HOD, AA, PRINCIPAL, STUDENT (6 roles)
- 5 users (one per role) with known credentials
- UserRole assignments
- 1 Department and 1 Program
- 1 Subject
- 1 Syllabus draft (owned by Lecturer)

Usage:
    python -m scripts.seed_mvp
    or
    python scripts/seed_mvp.py
"""
import sys
from pathlib import Path
# Bootstrap: ensure backend/src is in sys.path
_script_dir = Path(__file__).resolve().parent
_src_dir = _script_dir.parent
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

# Load environment variables from .env file
from dotenv import load_dotenv
env_path = _src_dir / '.env'
if not env_path.exists():
    # Try parent directory (backend/)
    env_path = _src_dir.parent / '.env'
load_dotenv(dotenv_path=env_path if env_path.exists() else None)

from config import Config
from infrastructure.databases.base import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from infrastructure.models.role import Role
from infrastructure.models.user import User
from infrastructure.models.user_role import UserRole
from infrastructure.models.department import Department
from infrastructure.models.program import Program
from infrastructure.models.subject import Subject
from infrastructure.models.syllabus import Syllabus
from infrastructure.models.syllabus_version import SyllabusVersion
from werkzeug.security import generate_password_hash
from datetime import datetime

# Standardized role names - exactly 6 roles: ADMIN, LECTURER, HOD, AA, PRINCIPAL, STUDENT
ROLES = ['ADMIN', 'LECTURER', 'HOD', 'AA', 'PRINCIPAL', 'STUDENT']

# User data: (username, password, full_name, email, role_name)
USERS = [
    ('lecturer', 'lecturer123', 'Dr. John Lecturer', 'lecturer@university.edu', 'LECTURER'),
    ('hod', 'hod123', 'Prof. Jane HOD', 'hod@university.edu', 'HOD'),
    ('aa', 'aa123', 'Dr. Bob Academic Affairs', 'aa@university.edu', 'AA'),
    ('admin', 'admin123', 'System Administrator', 'admin@university.edu', 'ADMIN'),
    ('principal', 'principal123', 'Principal User', 'principal@university.edu', 'PRINCIPAL'),
    ('student', 'student123', 'Student User', 'student@university.edu', 'STUDENT'),
]


def seed_roles(db):
    """Create all standard roles if they don't exist. Upsert logic: update name if exists."""
    created_roles = {}
    for role_name in ROLES:
        existing_role = db.query(Role).filter_by(role_name=role_name).first()
        if not existing_role:
            role = Role(role_name=role_name)
            db.add(role)
            db.flush()  # Get role_id
            created_roles[role_name] = role
            print(f"  [OK] Created role: {role_name}")
        else:
            # Update role name if different (defensive - should not happen)
            if existing_role.role_name != role_name:
                existing_role.role_name = role_name
                db.flush()
                print(f"  [OK] Updated role name: {role_name}")
            else:
                print(f"  - Role already exists: {role_name}")
            created_roles[role_name] = existing_role
    return created_roles


def seed_users(db, roles):
    """Create users with their roles."""
    created_users = {}
    for username, password, full_name, email, role_name in USERS:
        # Check if user already exists
        existing_user = db.query(User).filter_by(username=username).first()
        if existing_user:
            created_users[username] = existing_user
            print(f"  - User already exists: {username}")
            continue
        
        # Create user
        user = User(
            username=username,
            password_hash=generate_password_hash(password),
            full_name=full_name,
            email=email,
            status='active',
            created_at=datetime.utcnow()
        )
        db.add(user)
        db.flush()  # Get user_id
        
        # Assign role
        role = roles[role_name]
        user_role = UserRole(
            user_id=user.user_id,
            role_id=role.role_id
        )
        db.add(user_role)
        created_users[username] = user
        print(f"  [OK] Created user: {username} (ID: {user.user_id}) with role: {role_name}")
    
    return created_users


def seed_department(db):
    """Create a test department."""
    existing_dept = db.query(Department).filter_by(code='CS').first()
    if existing_dept:
        print(f"  - Department already exists: {existing_dept.name}")
        return existing_dept
    
    department = Department(
        code='CS',
        name='Computer Science'
    )
    db.add(department)
    db.flush()
    print(f"  [OK] Created department: {department.name} (ID: {department.department_id})")
    return department


def seed_program(db, department):
    """Create a test program."""
    existing_program = db.query(Program).filter_by(code='CS-BS').first()
    if existing_program:
        print(f"  - Program already exists: {existing_program.name}")
        return existing_program
    
    program = Program(
        department_id=department.department_id,
        code='CS-BS',
        name='Bachelor of Science in Computer Science'
    )
    db.add(program)
    db.flush()
    print(f"  [OK] Created program: {program.name} (ID: {program.program_id})")
    return program


def seed_subject(db, department):
    """Create a test subject."""
    existing_subject = db.query(Subject).filter_by(code='CS101').first()
    if existing_subject:
        print(f"  - Subject already exists: {existing_subject.name}")
        return existing_subject
    
    subject = Subject(
        department_id=department.department_id,
        code='CS101',
        name='Introduction to Computer Science',
        credits=3,
        status='active'
    )
    db.add(subject)
    db.flush()
    print(f"  [OK] Created subject: {subject.name} (ID: {subject.subject_id})")
    return subject


def seed_syllabus(db, subject, program, lecturer_user):
    """Create a test syllabus draft owned by lecturer with initial version."""
    # Check if syllabus already exists for this subject
    existing_syllabus = db.query(Syllabus).filter_by(
        subject_id=subject.subject_id,
        owner_lecturer_id=lecturer_user.user_id
    ).first()
    
    if existing_syllabus:
        print(f"  - Syllabus already exists: ID {existing_syllabus.syllabus_id}")
        return existing_syllabus
    
    # Create syllabus
    syllabus = Syllabus(
        subject_id=subject.subject_id,
        program_id=program.program_id,
        owner_lecturer_id=lecturer_user.user_id,
        current_version_id=None,  # Will be set after version creation
        lifecycle_status='DRAFT',
        created_at=datetime.utcnow()
    )
    db.add(syllabus)
    db.flush()
    
    # Create initial version (version_no=1)
    current_year = datetime.utcnow().year
    academic_year = f"{current_year}-{current_year + 1}"
    
    version = SyllabusVersion(
        syllabus_id=syllabus.syllabus_id,
        academic_year=academic_year,
        version_no=1,
        workflow_status='DRAFT',  # Match syllabus lifecycle_status
        submitted_at=None,
        approved_at=None,
        published_at=None,
        created_by=lecturer_user.user_id,
        created_at=datetime.utcnow()
    )
    db.add(version)
    db.flush()
    
    # Link version to syllabus
    syllabus.current_version_id = version.version_id
    db.flush()
    
    print(f"  [OK] Created syllabus draft: ID {syllabus.syllabus_id} (Status: DRAFT)")
    print(f"  [OK] Created initial version: ID {version.version_id} (version_no=1)")
    return syllabus


def seed_all():
    """Seed all MVP data."""
    print("=" * 60)
    print("SMD MVP Database Seeding Script")
    print("=" * 60)
    print()
    
    # Initialize database connection (standalone script, no Flask app)
    database_uri = Config.DATABASE_URI
    if not database_uri:
        import os
        database_uri = os.environ.get('DATABASE_URI')
        if not database_uri:
            raise ValueError(
                "DATABASE_URI must be set in environment.\n"
                "Options:\n"
                "  1. Set DATABASE_URI in your .env file (in backend/ or backend/src/ directory)\n"
                "  2. Set DATABASE_URI as environment variable"
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
    
    # Ensure tables exist
    print("Step 1: Verifying database tables...")
    Base.metadata.create_all(bind=engine)
    print("  [OK] Database tables verified/created")
    print()
    
    db = SessionLocal()
    try:
        # Seed roles
        print("Step 2: Seeding roles...")
        roles = seed_roles(db)
        db.commit()
        print()
        
        # Seed users
        print("Step 3: Seeding users...")
        users = seed_users(db, roles)
        db.commit()
        print()
        
        # Seed department
        print("Step 4: Seeding department...")
        department = seed_department(db)
        db.commit()
        print()
        
        # Seed program
        print("Step 5: Seeding program...")
        program = seed_program(db, department)
        db.commit()
        print()
        
        # Seed subject
        print("Step 6: Seeding subject...")
        subject = seed_subject(db, department)
        db.commit()
        print()
        
        # Seed syllabus
        print("Step 7: Seeding syllabus draft...")
        lecturer_user = users.get('lecturer')
        if lecturer_user:
            syllabus = seed_syllabus(db, subject, program, lecturer_user)
            db.commit()
        else:
            print("  ⚠ Lecturer user not found, skipping syllabus creation")
        print()
        
        # Print credentials summary
        print("=" * 60)
        print("SEEDING COMPLETE - User Credentials")
        print("=" * 60)
        print()
        print("The following users have been created:")
        print()
        for username, password, full_name, email, role_name in USERS:
            user = users.get(username)
            if user:
                print(f"  Username: {username:12} | Password: {password:15} | Role: {role_name:10} | ID: {user.user_id}")
            else:
                print(f"  Username: {username:12} | Password: {password:15} | Role: {role_name:10} | (Already exists)")
        print()
        print("=" * 60)
        print("You can now test the SMD workflow:")
        print("  1. Login as 'lecturer' to create/submit syllabi")
        print("  2. Login as 'hod' to approve/reject at department level")
        print("  3. Login as 'aa' to approve/reject at academic level")
        print("  4. Login as 'admin' or 'principal' to publish syllabi")
        print("=" * 60)
        
    except Exception as e:
        db.rollback()
        print()
        print("=" * 60)
        print(f"ERROR: Seeding failed: {str(e)}")
        print("=" * 60)
        raise
    finally:
        db.close()


if __name__ == '__main__':
    seed_all()

