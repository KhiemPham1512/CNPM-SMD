"""
Demo Seeding Script for SMD System

Creates minimal data required for demo:
- All 6 roles (if not exist)
- 1 Admin user (if not exist)
- 1 Lecturer user (if not exist)
- 2-3 Subjects (if not exist)
- 2-3 Programs (if not exist)

Uses "seed if not exists" logic - safe to run multiple times.

Usage:
    python -m scripts.seed_demo
    or
    python scripts/seed_demo.py
"""
import sys
from pathlib import Path

# Bootstrap: ensure backend/src is in sys.path
_script_dir = Path(__file__).resolve().parent
_src_dir = _script_dir.parent
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

# Load environment variables
from dotenv import load_dotenv
env_path = _src_dir / '.env'
if not env_path.exists():
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
from werkzeug.security import generate_password_hash
from datetime import datetime

# Constants matching domain/constants.py
ROLES = ['ADMIN', 'LECTURER', 'HOD', 'AA', 'PRINCIPAL', 'STUDENT']

# Demo users: (username, password, full_name, email, role_name)
DEMO_USERS = [
    ('admin', 'admin123', 'System Administrator', 'admin@university.edu', 'ADMIN'),
    ('lecturer', 'lecturer123', 'Dr. John Lecturer', 'lecturer@university.edu', 'LECTURER'),
]

# Demo subjects: (code, name, credits)
DEMO_SUBJECTS = [
    ('CNPM', 'Công nghệ phần mềm', 3),
    ('CSDL', 'Cơ sở dữ liệu', 3),
    ('LTTQ', 'Lập trình truyền thống', 3),
]

# Demo programs: (code, name)
DEMO_PROGRAMS = [
    ('SE', 'Software Engineering'),
    ('IT', 'Information Technology'),
    ('CS', 'Computer Science'),
]


def seed_roles(db):
    """Create all roles if they don't exist."""
    created_roles = {}
    for role_name in ROLES:
        existing_role = db.query(Role).filter_by(role_name=role_name).first()
        if not existing_role:
            role = Role(role_name=role_name)
            db.add(role)
            db.flush()
            created_roles[role_name] = role
            print(f"  [OK] Created role: {role_name}")
        else:
            created_roles[role_name] = existing_role
            print(f"  - Role already exists: {role_name}")
    return created_roles


def seed_users(db, roles):
    """Create demo users if they don't exist."""
    created_users = {}
    for username, password, full_name, email, role_name in DEMO_USERS:
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
        db.flush()
        
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
    """Create a default department if it doesn't exist."""
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


def seed_programs(db, department):
    """Create demo programs if they don't exist."""
    created_programs = {}
    for code, name in DEMO_PROGRAMS:
        existing_program = db.query(Program).filter_by(code=code).first()
        if existing_program:
            created_programs[code] = existing_program
            print(f"  - Program already exists: {name}")
            continue
        
        program = Program(
            department_id=department.department_id,
            code=code,
            name=name
        )
        db.add(program)
        db.flush()
        created_programs[code] = program
        print(f"  [OK] Created program: {name} (ID: {program.program_id})")
    
    return created_programs


def seed_subjects(db, department):
    """Create demo subjects if they don't exist."""
    created_subjects = {}
    for code, name, credits in DEMO_SUBJECTS:
        existing_subject = db.query(Subject).filter_by(code=code).first()
        if existing_subject:
            created_subjects[code] = existing_subject
            print(f"  - Subject already exists: {name}")
            continue
        
        subject = Subject(
            department_id=department.department_id,
            code=code,
            name=name,
            credits=credits,
            status='active'
        )
        db.add(subject)
        db.flush()
        created_subjects[code] = subject
        print(f"  [OK] Created subject: {name} (ID: {subject.subject_id})")
    
    return created_subjects


def seed_all():
    """Seed all demo data."""
    print("=" * 60)
    print("SMD Demo Database Seeding Script")
    print("=" * 60)
    print()
    
    # Initialize database connection
    database_uri = Config.DATABASE_URI
    if not database_uri:
        import os
        database_uri = os.environ.get('DATABASE_URI')
        if not database_uri:
            raise ValueError(
                "DATABASE_URI must be set in environment.\n"
                "Set DATABASE_URI in your .env file (in backend/ or backend/src/ directory)"
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
        print("Step 3: Seeding demo users...")
        users = seed_users(db, roles)
        db.commit()
        print()
        
        # Seed department
        print("Step 4: Seeding department...")
        department = seed_department(db)
        db.commit()
        print()
        
        # Seed programs
        print("Step 5: Seeding programs...")
        programs = seed_programs(db, department)
        db.commit()
        print()
        
        # Seed subjects
        print("Step 6: Seeding subjects...")
        subjects = seed_subjects(db, department)
        db.commit()
        print()
        
        # Print credentials summary
        print("=" * 60)
        print("SEEDING COMPLETE - Demo Credentials")
        print("=" * 60)
        print()
        print("The following users have been created:")
        print()
        for username, password, full_name, email, role_name in DEMO_USERS:
            user = users.get(username)
            if user:
                print(f"  Username: {username:12} | Password: {password:15} | Role: {role_name}")
            else:
                print(f"  Username: {username:12} | Password: {password:15} | Role: {role_name} (Already exists)")
        print()
        print("=" * 60)
        print("Demo data ready for testing!")
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
