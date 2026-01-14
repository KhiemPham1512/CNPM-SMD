# SMD - Syllabus Management & Digitization System

Hệ thống quản lý và số hóa đề cương học phần cho trường đại học.

## 📋 Tổng quan

Dự án bao gồm:
- **Backend**: Flask REST API (Python) với Clean Architecture
- **Frontend**: React + TypeScript + TailwindCSS
- **Database**: Microsoft SQL Server (MSSQL)

## 🚀 Hướng dẫn chạy toàn bộ dự án

### Yêu cầu hệ thống

1. **Python 3.8+** (cho backend)
2. **Node.js 18+ và npm** (cho frontend)
3. **Docker** (để chạy MSSQL Server) hoặc MSSQL Server đã cài đặt
4. **Git** (để clone repository)

---

## BƯỚC 1: Setup Backend

### 1.1. Tạo và kích hoạt Virtual Environment

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

### 1.2. Cài đặt dependencies

```powershell
# Đảm bảo đang ở trong backend/src và virtual environment đã được kích hoạt
pip install -r requirements.txt
```

### 1.3. Khởi động MSSQL Server (Docker)

```powershell
# Chạy MSSQL Server container
docker run -e "ACCEPT_EULA=Y" -e "MSSQL_SA_PASSWORD=Aa@123456" -p 1433:1433 --name sql1 --hostname sql1 -d mcr.microsoft.com/mssql/server:2025-latest
```

Đợi 30-60 giây để SQL Server khởi động. Kiểm tra logs:
```powershell
docker logs sql1
```

**Lưu ý:** Nếu container `sql1` đã tồn tại, bạn có thể:
- Sử dụng container hiện có: `docker start sql1`
- Hoặc xóa và tạo mới: `docker rm -f sql1` rồi chạy lại lệnh trên

### 1.4. Tạo file .env cho Backend

```powershell
# Từ thư mục backend/src
Copy-Item .env.example .env
```

Chỉnh sửa file `.env` trong `backend/src/`:

```env
FLASK_ENV=development
DEBUG=True
SECRET_KEY=your-secret-key-change-this-in-production
DATABASE_URI=mssql+pymssql://sa:Aa%40123456@127.0.0.1:1433/smd
```

**Quan trọng:**
- URL encode ký tự đặc biệt trong password (ví dụ: `@` thành `%40`)
- Đảm bảo database `smd` đã được tạo (hoặc thay đổi tên database trong connection string)

### 1.5. Kiểm tra kết nối Database

```powershell
# Từ backend/src, với virtual environment đã kích hoạt
python -m scripts.test_connection
```

### 1.6. Seed Database (Tạo dữ liệu mẫu)

```powershell
# Từ backend/src, với virtual environment đã kích hoạt
python -m scripts.seed_mvp
```

Script này sẽ tạo:
- 6 roles: ADMIN, LECTURER, HOD, AA, PRINCIPAL, STUDENT
- 6 users demo với credentials:
  - `admin` / `admin123` (ADMIN)
  - `lecturer` / `lecturer123` (LECTURER)
  - `hod` / `hod123` (HOD)
  - `aa` / `aa123` (AA)
  - `principal` / `principal123` (PRINCIPAL)
  - `student` / `student123` (STUDENT)
- Dữ liệu mẫu: Department, Program, Subject, Syllabus

### 1.7. Chạy Backend

```powershell
# Từ backend/src, với virtual environment đã kích hoạt
python app.py
```

Hoặc sử dụng Flask CLI:
```powershell
flask run --host=0.0.0.0 --port=9999
```

Backend sẽ chạy tại: **http://127.0.0.1:9999**

**Kiểm tra:**
- Swagger UI: http://127.0.0.1:9999/docs
- API Spec: http://127.0.0.1:9999/swagger.json

---

## BƯỚC 2: Setup Frontend

### 2.1. Cài đặt dependencies

Mở terminal mới (giữ backend đang chạy):

```powershell
# Di chuyển vào thư mục frontend
cd frontend

# Cài đặt dependencies
npm install
```

### 2.2. Tạo file .env cho Frontend

Tạo file `.env` trong thư mục `frontend/`:

```env
VITE_API_URL=http://localhost:9999
```

**Lưu ý:** Nếu backend chạy ở port khác, thay đổi URL tương ứng.

### 2.3. Chạy Frontend

```powershell
# Từ thư mục frontend
npm run dev
```

Frontend sẽ chạy tại: **http://localhost:3000**

---

## BƯỚC 3: Sử dụng ứng dụng

### 3.1. Đăng nhập

1. Mở trình duyệt và truy cập: **http://localhost:3000**
2. Sử dụng một trong các tài khoản sau:

| Username | Password | Role | Mô tả |
|----------|----------|------|-------|
| `admin` | `admin123` | ADMIN | Quản trị hệ thống, quản lý users |
| `lecturer` | `lecturer123` | LECTURER | Tạo và quản lý đề cương |
| `hod` | `hod123` | HOD | Duyệt đề cương cấp khoa |
| `aa` | `aa123` | AA | Duyệt đề cương cấp phòng đào tạo |
| `principal` | `principal123` | PRINCIPAL | Xuất bản đề cương |
| `student` | `student123` | STUDENT | Xem đề cương đã xuất bản |

### 3.2. Các tính năng chính

- **Dashboard**: Tổng quan về số lượng đề cương theo trạng thái
- **Syllabus Management**: Tạo, chỉnh sửa, xem chi tiết đề cương
- **Workflow**: Quy trình duyệt đề cương (DRAFT → PENDING_REVIEW → PENDING_APPROVAL → APPROVED → PUBLISHED)
- **User Management** (Admin only): Quản lý người dùng và phân quyền
- **Public Search**: Tìm kiếm và xem đề cương đã xuất bản (Student/Public)

---

## 📁 Cấu trúc dự án

```
CNPM_SMD/
├── backend/              # Backend Flask API
│   ├── src/
│   │   ├── api/          # API layer (controllers, routes, schemas)
│   │   ├── domain/       # Domain layer (models, services)
│   │   ├── infrastructure/  # Infrastructure layer (database, repositories)
│   │   ├── services/     # Application services
│   │   ├── scripts/      # Database scripts (seed, cleanup)
│   │   ├── app.py        # Flask app entry point
│   │   ├── config.py     # Configuration
│   │   └── requirements.txt
│   └── README.md
│
├── frontend/             # Frontend React App
│   ├── src/
│   │   ├── app/          # App config (router, providers)
│   │   ├── components/   # Reusable components
│   │   ├── features/     # Feature modules
│   │   ├── services/     # API services
│   │   ├── types/        # TypeScript types
│   │   └── utils/        # Utilities
│   ├── package.json
│   └── README.md
│
└── README.md            # File này
```

---

## 🔧 Troubleshooting

### Backend không kết nối được Database

1. **Kiểm tra SQL Server đang chạy:**
   ```powershell
   docker ps | Select-String sql
   ```

2. **Kiểm tra port 1433:**
   ```powershell
   Test-NetConnection -ComputerName 127.0.0.1 -Port 1433
   ```

3. **Kiểm tra DATABASE_URI trong .env:**
   - Đảm bảo password đã được URL encode
   - Kiểm tra username/password đúng
   - Kiểm tra database name tồn tại

### Frontend không kết nối được Backend

1. **Kiểm tra backend đang chạy:**
   - Truy cập http://127.0.0.1:9999/docs
   - Nếu không mở được, backend chưa chạy

2. **Kiểm tra VITE_API_URL trong .env:**
   - Đảm bảo URL đúng với port backend
   - Không có dấu `/` ở cuối URL

3. **Kiểm tra CORS:**
   - Backend đã cấu hình CORS cho `http://localhost:3000`
   - Nếu dùng port khác, cần cập nhật `CORS_ORIGINS` trong `backend/src/config.py`

### Port đã được sử dụng

**Backend (port 9999):**
- Thay đổi port trong `backend/src/app.py`:
  ```python
  app.run(host='0.0.0.0', port=9999, debug=True)  # Đổi 9999 thành port khác
  ```
- Cập nhật `VITE_API_URL` trong frontend `.env`

**Frontend (port 3000):**
- Thay đổi port trong `frontend/vite.config.ts`:
  ```typescript
  server: {
    port: 3000,  // Đổi thành port khác
  }
  ```

### Lỗi JWT Token

- Token hết hạn sau 2 giờ, đăng nhập lại để lấy token mới
- Đảm bảo `SECRET_KEY` trong backend `.env` không thay đổi giữa các lần chạy

---

## 📚 Tài liệu tham khảo

- **Tài liệu đầy đủ**: Xem `docs/README.md` để biết cấu trúc tài liệu
- **Hướng dẫn triển khai**: Xem `docs/09_deployment.md` để biết chi tiết setup
- **API Documentation**: Truy cập http://127.0.0.1:9999/docs khi backend đang chạy

---

## 🛠️ Development Tips

1. **Backend auto-reload**: Flask chạy ở debug mode, tự động reload khi code thay đổi
2. **Frontend hot-reload**: Vite tự động reload khi code thay đổi
3. **Swagger UI**: Sử dụng http://127.0.0.1:9999/docs để test API trực tiếp
4. **Database changes**: Sử dụng migrations hoặc set `AUTO_CREATE_TABLES=True` trong development

---

## 📝 Ghi chú

- Tất cả mật khẩu demo chỉ dùng cho development
- Trong production, cần:
  - Đặt `DEBUG=False`
  - Sử dụng `SECRET_KEY` mạnh
  - Cấu hình CORS đúng với domain frontend
  - Sử dụng WSGI server (gunicorn, uwsgi) thay vì Flask dev server

---

## ✅ Checklist chạy dự án

- [ ] Python 3.8+ đã cài đặt
- [ ] Node.js 18+ và npm đã cài đặt
- [ ] Docker đã cài đặt và chạy
- [ ] MSSQL Server container đang chạy
- [ ] Backend virtual environment đã tạo và kích hoạt
- [ ] Backend dependencies đã cài đặt (`pip install -r requirements.txt`)
- [ ] Backend `.env` đã tạo và cấu hình đúng
- [ ] Database connection test thành công
- [ ] Database đã được seed (`python -m scripts.seed_mvp`)
- [ ] Backend đang chạy tại http://127.0.0.1:9999
- [ ] Frontend dependencies đã cài đặt (`npm install`)
- [ ] Frontend `.env` đã tạo với `VITE_API_URL` đúng
- [ ] Frontend đang chạy tại http://localhost:3000
- [ ] Đăng nhập thành công với một trong các tài khoản demo

---

**Chúc bạn code vui vẻ! 🚀**
