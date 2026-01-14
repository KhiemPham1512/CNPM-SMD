"""
Script để lấy Supabase connection string từ Docker container.
"""
import subprocess
import sys
from pathlib import Path

def get_supabase_db_info():
    """Lấy thông tin database từ Supabase container."""
    try:
        # Lấy environment variables từ container
        result = subprocess.run(
            ['docker', 'exec', 'supabase-db', 'env'],
            capture_output=True,
            text=True,
            check=True
        )
        
        env_vars = {}
        for line in result.stdout.split('\n'):
            if '=' in line and line.startswith(('POSTGRES_', 'PG')):
                key, value = line.split('=', 1)
                env_vars[key] = value
        
        return env_vars
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        return None

def get_port_mapping():
    """Lấy port mapping từ Docker."""
    try:
        result = subprocess.run(
            ['docker', 'port', 'supabase-db', '5432/tcp'],
            capture_output=True,
            text=True,
            check=True
        )
        if result.stdout.strip():
            # Format: 0.0.0.0:54322
            port = result.stdout.strip().split(':')[1]
            return port
        return None
    except subprocess.CalledProcessError:
        return None

def main():
    print("=" * 60)
    print("Supabase Connection String Helper")
    print("=" * 60)
    print()
    
    # Kiểm tra container đang chạy
    try:
        result = subprocess.run(
            ['docker', 'ps', '--filter', 'name=supabase-db', '--format', '{{.Names}}'],
            capture_output=True,
            text=True,
            check=True
        )
        if not result.stdout.strip():
            print("[ERROR] Container 'supabase-db' khong dang chay")
            print("   Chay: docker ps | Select-String supabase-db")
            return
    except subprocess.CalledProcessError:
        print("[ERROR] Khong the kiem tra Docker containers")
        return
    
    print("[OK] Container 'supabase-db' dang chay")
    print()
    
    # Lấy thông tin từ container
    env_vars = get_supabase_db_info()
    if not env_vars:
        print("[ERROR] Khong the lay thong tin tu container")
        return
    
    # Lấy thông tin cần thiết
    password = env_vars.get('POSTGRES_PASSWORD') or env_vars.get('PGPASSWORD', 'Aa@12345ssdg')
    database = env_vars.get('POSTGRES_DB') or env_vars.get('PGDATABASE', 'postgres')
    user = env_vars.get('POSTGRES_USER') or env_vars.get('PGUSER', 'postgres')
    
    # URL encode password
    password_encoded = password.replace('@', '%40').replace('#', '%23')
    
    # Lấy port mapping
    port = get_port_mapping()
    if not port:
        print("[WARNING] Port khong duoc expose ra ngoai")
        print()
        print("Có 2 cách:")
        print()
        print("1. Dùng Supabase CLI (Khuyến nghị):")
        print("   npm install -g supabase")
        print("   cd backend")
        print("   supabase status")
        print("   # Copy 'DB URL' từ output")
        print()
        print("2. Expose port thủ công:")
        print("   # Cần stop và recreate container với port mapping")
        print()
        print("Thông tin từ container:")
        print(f"   User: {user}")
        print(f"   Password: {password}")
        print(f"   Database: {database}")
        print()
        print("Connection string (cần port):")
        print(f"   postgresql+psycopg2://{user}:{password_encoded}@127.0.0.1:[PORT]/{database}")
        return
    
    # Tạo connection string
    connection_string = f"postgresql+psycopg2://{user}:{password_encoded}@127.0.0.1:{port}/{database}"
    
    print("[OK] Thong tin ket noi:")
    print()
    print(f"   User: {user}")
    print(f"   Password: {password} (encoded: {password_encoded})")
    print(f"   Database: {database}")
    print(f"   Port: {port}")
    print()
    print("=" * 60)
    print("DATABASE_URI cho backend/.env:")
    print("=" * 60)
    print()
    print(connection_string)
    print()
    print("=" * 60)
    print()
    print("Copy dòng trên vào file backend/.env:")
    print("   DATABASE_URI=" + connection_string)

if __name__ == '__main__':
    main()
