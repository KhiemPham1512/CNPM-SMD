"""
Test Database Connection Script

This script tests the database connection to help diagnose connection issues.

Usage:
    python -m scripts.test_connection
    or
    python scripts/test_connection.py
"""
import sys
from pathlib import Path
# Bootstrap: ensure backend/src is in sys.path
_script_dir = Path(__file__).resolve().parent
_src_dir = _script_dir.parent
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

from config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, ProgrammingError

def test_connection():
    """Test database connection."""
    print("=" * 60)
    print("Database Connection Test")
    print("=" * 60)
    print()
    
    database_uri = Config.DATABASE_URI
    print(f"Connection URI: {database_uri.replace(Config.DATABASE_URI.split('@')[0].split('//')[1] if '@' in Config.DATABASE_URI else '', '***')}")
    print()
    
    try:
        print("Step 1: Creating engine with timeout settings...")
        engine = create_engine(
            database_uri,
            connect_args={
                'timeout': 10,
                'login_timeout': 10,
            },
            pool_pre_ping=True
        )
        print("  ✓ Engine created")
        
        print("Step 2: Testing connection (timeout: 10s)...")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT @@VERSION as version"))
            version = result.fetchone()[0]
            print(f"  ✓ Connected successfully")
            print(f"  SQL Server version: {version[:50]}...")
        
        print("Step 3: Testing database access...")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT DB_NAME() as db_name"))
            db_name = result.fetchone()[0]
            print(f"  ✓ Current database: {db_name}")
        
        print()
        print("=" * 60)
        print("✓ Connection test PASSED")
        print("=" * 60)
        return True
        
    except OperationalError as e:
        print()
        print("=" * 60)
        print("✗ Connection test FAILED - Operational Error")
        print("=" * 60)
        error_msg = str(e)
        print(f"Error: {error_msg}")
        print()
        
        if "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
            print("⚠ CONNECTION TIMEOUT DETECTED")
            print()
            print("Possible causes:")
            print("  1. SQL Server is not running")
            print("  2. SQL Server is starting up (wait 30-60 seconds)")
            print("  3. Firewall blocking port 1433")
            print("  4. Wrong host/port")
            print()
            print("Troubleshooting steps:")
            print("  1. Check if SQL Server container is running:")
            print("     docker ps | grep sql")
            print()
            print("  2. Check if port 1433 is accessible:")
            print("     telnet 127.0.0.1 1433")
            print("     (or use: netstat -an | findstr 1433)")
            print()
            print("  3. Start SQL Server if not running:")
            print('     docker run -e "ACCEPT_EULA=Y" -e "MSSQL_SA_PASSWORD=Aa@123456" -p 1433:1433 --name sql1 --hostname sql1 -d mcr.microsoft.com/mssql/server:2025-latest')
            print()
            print("  4. Wait for SQL Server to be ready (check logs):")
            print("     docker logs sql1")
        else:
            print("Possible causes:")
            print("  1. SQL Server is not running")
            print("  2. Wrong host/port (check 127.0.0.1:1433)")
            print("  3. Wrong username/password")
            print("  4. Firewall blocking connection")
            print()
            print("To start SQL Server in Docker:")
            print('  docker run -e "ACCEPT_EULA=Y" -e "MSSQL_SA_PASSWORD=Aa@123456" -p 1433:1433 --name sql1 --hostname sql1 -d mcr.microsoft.com/mssql/server:2025-latest')
        return False
        
    except ProgrammingError as e:
        print()
        print("=" * 60)
        print("✗ Connection test FAILED - Programming Error")
        print("=" * 60)
        print(f"Error: {str(e)}")
        print()
        print("Possible causes:")
        print("  1. Database does not exist")
        print("  2. User does not have permission")
        print()
        print("To create database, run:")
        print("  python -m scripts.reset_db")
        return False
        
    except Exception as e:
        print()
        print("=" * 60)
        print("✗ Connection test FAILED - Unexpected Error")
        print("=" * 60)
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_connection()
    sys.exit(0 if success else 1)
