# Triển khai & Deployment

---

## 1. Prerequisites

### 1.1. Yêu cầu Hệ thống

- **Python 3.8+** (cho backend)
- **Node.js 18+ và npm** (cho frontend)
- **Docker** (để chạy MSSQL Server) hoặc MSSQL Server đã cài đặt
- **Supabase** (local hoặc cloud, cho file storage - optional)
- **Git** (để clone repository)

### 1.2. Kiểm tra Cài đặt

```powershell
# Kiểm tra Python
python --version
# Expected: Python 3.8.x hoặc cao hơn

# Kiểm tra Node.js
node --version
# Expected: v18.x.x hoặc cao hơn

# Kiểm tra npm
npm --version
# Expected: 9.x.x hoặc cao hơn

# Kiểm tra Docker
docker --version
# Expected: Docker version 20.x.x hoặc cao hơn
```

---

## 2. Backend Setup

### 2.1. Tạo Virtual Environment

```powershell
# Di chuyển vào thư mục backend/src
cd backend\src

# Tạo virtual environment (nếu chưa có)
python -m venv ..\..\.venv

# Kích hoạt virtual environment
..\..\.venv\Scripts\Activate.ps1
```

**Lưu ý:** Nếu gặp lỗi execution policy:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 2.2. Cài đặt Dependencies

```powershell
# Đảm bảo đang ở trong backend/src và virtual environment đã được kích hoạt
pip install -r requirements.txt
```

**Key Dependencies:**
- Flask 2.0+
- SQLAlchemy 1.4+
- PyJWT 2.8+
- Marshmallow 3.x
- pymssql 2.2+ (cho MSSQL)
- supabase 2.0+ (cho file storage)

### 2.3. Khởi động MSSQL Server (Docker)

```powershell
# Chạy MSSQL Server container
docker run -e "ACCEPT_EULA=Y" -e "MSSQL_SA_PASSWORD=Aa@123456" -p 1433:1433 --name sql1 --hostname sql1 -d mcr.microsoft.com/mssql/server:2025-latest
```

Đợi 30-60 giây để SQL Server khởi động. Kiểm tra logs:
```powershell
docker logs sql1
```

**Lưu ý:** Nếu container `sql1` đã tồn tại:
- Sử dụng container hiện có: `docker start sql1`
- Hoặc xóa và tạo mới: `docker rm -f sql1` rồi chạy lại lệnh trên

### 2.4. Tạo file .env cho Backend

**Location:** `backend/.env` (hoặc `backend/src/.env`)

```env
# Flask Configuration
FLASK_ENV=development
DEBUG=True
SECRET_KEY=your-secret-key-change-this-in-production

# Database Configuration
DATABASE_URI=mssql+pymssql://sa:Aa%40123456@127.0.0.1:1433/smd

# File Storage (Optional)
FILE_STORAGE_ENABLED=false
# Nếu enable, cần set các biến sau:
# SUPABASE_URL=http://localhost:8000
# SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
# SUPABASE_BUCKET=syllabus-files
# SUPABASE_SIGNED_URL_EXPIRES_IN=3600
# MAX_UPLOAD_MB=20

# Database Auto-create (Development only)
AUTO_CREATE_TABLES=false
```

**Quan trọng:**
- URL encode ký tự đặc biệt trong password (ví dụ: `@` thành `%40`)
- Đảm bảo database `smd` đã được tạo (hoặc thay đổi tên database trong connection string)
- `FILE_STORAGE_ENABLED=false` mặc định (set `true` nếu muốn dùng file storage)

### 2.5. Kiểm tra Kết nối Database

```powershell
# Từ backend/src, với virtual environment đã kích hoạt
python -m scripts.test_connection
```

**Expected output:**
```
Database connection successful!
Connection string: mssql+pymssql://sa:***@127.0.0.1:1433/smd
```

### 2.6. Seed Database (Tạo dữ liệu mẫu)

```powershell
# Từ backend/src, với virtual environment đã kích hoạt
python -m scripts.seed_mvp
```

**Script này sẽ tạo:**
- 6 roles: ADMIN, LECTURER, HOD, AA, PRINCIPAL, STUDENT
- 6 users demo với credentials:
  - `admin` / `admin123` (ADMIN)
  - `lecturer` / `lecturer123` (LECTURER)
  - `hod` / `hod123` (HOD)
  - `aa` / `aa123` (AA)
  - `principal` / `principal123` (PRINCIPAL)
  - `student` / `student123` (STUDENT)
- Dữ liệu mẫu: Department, Program, Subject, Syllabus

### 2.7. Chạy Backend

```powershell
# Từ backend/src, với virtual environment đã kích hoạt
python app.py
```

Hoặc sử dụng Flask CLI:
```powershell
flask run --host=0.0.0.0 --port=9999
```

**Backend sẽ chạy tại:** **http://127.0.0.1:9999**

**Kiểm tra:**
- Swagger UI: http://127.0.0.1:9999/docs
- API Spec: http://127.0.0.1:9999/swagger.json
- Health check: http://127.0.0.1:9999/files/health

**Expected logs:**
```
Loaded .env from: e:\CNPM_SMD\backend\.env
Loaded configuration: DevelopmentConfig
File storage: DISABLED (set FILE_STORAGE_ENABLED=true to enable)
Database initialized successfully
 * Running on http://127.0.0.1:9999
```

---

## 3. Frontend Setup

### 3.1. Cài đặt Dependencies

Mở terminal mới (giữ backend đang chạy):

```powershell
# Di chuyển vào thư mục frontend
cd frontend

# Cài đặt dependencies
npm install
```

### 3.2. Tạo file .env cho Frontend

**Location:** `frontend/.env`

```env
VITE_API_URL=http://localhost:9999
```

**Lưu ý:**
- Nếu backend chạy ở port khác, thay đổi URL tương ứng
- Không có dấu `/` ở cuối URL
- Sau khi tạo/sửa `.env`, restart dev server

### 3.3. Chạy Frontend

```powershell
# Từ thư mục frontend
npm run dev
```

**Frontend sẽ chạy tại:** **http://localhost:3000**

**Lưu ý:** Nếu port 3000 đã được sử dụng, Vite sẽ tự động dùng port 3002.

---

## 4. Supabase Setup (Optional - cho File Storage)

### 4.1. Local Supabase

**Option A: Supabase CLI (Recommended)**

```powershell
# Cài Supabase CLI
npm install -g supabase

# Start Supabase local
supabase start

# Lấy thông tin
supabase status
```

**Output sẽ hiển thị:**
- API URL: `http://localhost:8000`
- Service Role Key: (từ `.env` của Supabase)

**Option B: Docker Compose**

```powershell
# Từ project root
docker-compose -f docker-compose-supabase.yml up -d
```

### 4.2. Tạo Bucket

**Using Supabase Studio:**
1. Mở http://localhost:3000 (Supabase Studio)
2. Navigate to **Storage**
3. Click **New bucket**
4. Name: `syllabus-files`
5. **Public bucket:** ❌ **UNCHECKED** (private)
6. Click **Create bucket**

**Using CLI:**
```powershell
supabase storage create syllabus-files --public false
```

### 4.3. Cập nhật Backend .env

Thêm vào `backend/.env`:

```env
FILE_STORAGE_ENABLED=true
SUPABASE_URL=http://localhost:8000
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_BUCKET=syllabus-files
SUPABASE_SIGNED_URL_EXPIRES_IN=3600
MAX_UPLOAD_MB=20
```

**Restart backend** sau khi cập nhật `.env`.

### 4.4. Verify File Storage

```powershell
# Check health
curl http://localhost:9999/files/health

# Expected:
{
  "success": true,
  "data": {
    "enabled": true,
    "configured": true,
    "provider": "supabase",
    "bucket": "syllabus-files"
  }
}
```

---

## 5. Running Application

### 5.1. Start Order

1. **Start MSSQL Server:**
   ```powershell
   docker start sql1
   ```

2. **Start Backend:**
   ```powershell
   cd backend\src
   ..\..\.venv\Scripts\Activate.ps1
   python app.py
   ```

3. **Start Frontend:**
   ```powershell
   cd frontend
   npm run dev
   ```

4. **Start Supabase (nếu dùng file storage):**
   ```powershell
   supabase start
   ```

### 5.2. Verify

1. **Backend:** http://127.0.0.1:9999/docs (Swagger UI)
2. **Frontend:** http://localhost:3000
3. **Login:** Sử dụng một trong các tài khoản demo

---

## 6. Troubleshooting

### 6.1. Backend không kết nối được Database

**Symptoms:**
- Error: "Database service temporarily unavailable"
- Backend không start được

**Solutions:**

1. **Kiểm tra SQL Server đang chạy:**
   ```powershell
   docker ps | Select-String sql
   ```

2. **Nếu không chạy, start lại:**
   ```powershell
   docker start sql1
   ```

3. **Kiểm tra port 1433:**
   ```powershell
   Test-NetConnection -ComputerName 127.0.0.1 -Port 1433
   ```

4. **Kiểm tra DATABASE_URI trong .env:**
   - Đảm bảo password đã được URL encode (`@` → `%40`)
   - Kiểm tra username/password đúng
   - Kiểm tra database name tồn tại

5. **Tạo database nếu chưa có:**
   ```sql
   CREATE DATABASE smd;
   ```

### 6.2. Frontend không kết nối được Backend

**Symptoms:**
- Error: "Failed to connect to backend"
- Empty data trong tables

**Solutions:**

1. **Kiểm tra backend đang chạy:**
   - Truy cập http://127.0.0.1:9999/docs
   - Nếu không mở được, backend chưa chạy

2. **Kiểm tra VITE_API_URL trong .env:**
   - Đảm bảo URL đúng với port backend
   - Không có dấu `/` ở cuối URL
   - **Restart dev server** sau khi sửa `.env`

3. **Kiểm tra CORS:**
   - Backend đã cấu hình CORS cho `http://localhost:3000`
   - Nếu frontend chạy ở port khác (3002), cần cập nhật `CORS_ORIGINS` trong `backend/src/config.py`

### 6.3. File Storage Disabled

**Symptoms:**
- Frontend hiển thị "File storage is disabled"
- Upload button không hiển thị

**Solutions:**

1. **Check health endpoint:**
   ```powershell
   curl http://localhost:9999/files/health
   ```

2. **Nếu `enabled: false`:**
   - Set `FILE_STORAGE_ENABLED=true` trong `backend/.env`
   - Restart backend

3. **Nếu `configured: false`:**
   - Set đầy đủ: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_BUCKET`
   - Restart backend

4. **Verify Supabase đang chạy:**
   ```powershell
   supabase status
   ```

### 6.4. Port đã được sử dụng

**Backend (port 9999):**
- Thay đổi port trong `backend/src/app.py`:
  ```python
  app.run(host='0.0.0.0', port=9999, debug=True)  # Đổi 9999 thành port khác
  ```
- Cập nhật `VITE_API_URL` trong frontend `.env`

**Frontend (port 3000):**
- Vite tự động dùng port 3002 nếu 3000 bị chiếm
- Hoặc thay đổi port trong `frontend/vite.config.ts`:
  ```typescript
  server: {
    port: 3000,  // Đổi thành port khác
  }
  ```

### 6.5. Lỗi JWT Token

**Symptoms:**
- Error: "Token expired" hoặc "Invalid token"
- Tự động logout

**Solutions:**
- Token hết hạn sau 2 giờ, đăng nhập lại để lấy token mới
- Đảm bảo `SECRET_KEY` trong backend `.env` không thay đổi giữa các lần chạy

### 6.6. Database Connection Error

**Symptoms:**
- Error: "Database service temporarily unavailable"
- 503 errors

**Solutions:**

1. **Kiểm tra MSSQL container:**
   ```powershell
   docker ps
   docker logs sql1
   ```

2. **Kiểm tra connection string:**
   - Verify `DATABASE_URI` trong `.env`
   - Test connection: `python -m scripts.test_connection`

3. **Restart container:**
   ```powershell
   docker restart sql1
   ```

### 6.7. Build Errors

**Frontend:**
```powershell
cd frontend
npm run build
```

**Nếu có TypeScript errors:**
- Check `tsconfig.json`
- Verify all imports
- Run `npm install` again

**Backend:**
```powershell
cd backend\src
python -m py_compile app.py
```

---

## 7. Production Deployment (Notes)

### 7.1. Backend

**Không dùng Flask dev server trong production:**
- Sử dụng WSGI server: gunicorn, uwsgi
- Set `DEBUG=False`
- Sử dụng `SECRET_KEY` mạnh
- Cấu hình CORS đúng với domain frontend

**Example với gunicorn:**
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:9999 "app:create_app()"
```

### 7.2. Frontend

**Build for production:**
```powershell
cd frontend
npm run build
```

**Output:** `frontend/dist/` - Deploy folder này lên web server (Nginx, Apache, etc.)

### 7.3. Database

**Production database:**
- Không dùng `AUTO_CREATE_TABLES=True`
- Sử dụng migration tool (Alembic)
- Backup database thường xuyên

### 7.4. Environment Variables

**Production .env:**
```env
FLASK_ENV=production
DEBUG=False
SECRET_KEY=<strong-random-key>
DATABASE_URI=<production-database-uri>
FILE_STORAGE_ENABLED=true
SUPABASE_URL=<production-supabase-url>
SUPABASE_SERVICE_ROLE_KEY=<production-key>
CORS_ORIGINS=https://yourdomain.com
```

---

## 8. Quick Start Checklist

- [ ] Python 3.8+ đã cài đặt
- [ ] Node.js 18+ và npm đã cài đặt
- [ ] Docker đã cài đặt và chạy
- [ ] MSSQL Server container đang chạy (`docker start sql1`)
- [ ] Backend virtual environment đã tạo và kích hoạt
- [ ] Backend dependencies đã cài đặt (`pip install -r requirements.txt`)
- [ ] Backend `.env` đã tạo và cấu hình đúng
- [ ] Database connection test thành công (`python -m scripts.test_connection`)
- [ ] Database đã được seed (`python -m scripts.seed_mvp`)
- [ ] Backend đang chạy tại http://127.0.0.1:9999
- [ ] Swagger UI accessible (http://127.0.0.1:9999/docs)
- [ ] Frontend dependencies đã cài đặt (`npm install`)
- [ ] Frontend `.env` đã tạo với `VITE_API_URL` đúng
- [ ] Frontend đang chạy tại http://localhost:3000
- [ ] Đăng nhập thành công với một trong các tài khoản demo
- [ ] (Optional) Supabase đang chạy và file storage enabled

---

**Sau khi hoàn thành checklist, hệ thống đã sẵn sàng sử dụng!**
