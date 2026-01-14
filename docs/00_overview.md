# Tổng quan Hệ thống SMD

**Hệ thống Quản lý và Số hóa Đề cương Học phần (Syllabus Management & Digitization System)**

---

## 1. Giới thiệu

SMD là hệ thống quản lý đề cương học phần cho trường đại học, hỗ trợ quy trình số hóa và quản lý đề cương từ giai đoạn soạn thảo đến xuất bản.

### 1.1. Mục tiêu Đồ án

- **Số hóa quy trình quản lý đề cương:** Chuyển đổi từ quy trình thủ công sang hệ thống số
- **Quản lý workflow:** Hỗ trợ quy trình duyệt đề cương qua nhiều cấp (Khoa → Phòng Đào tạo → Hiệu trưởng)
- **Phân quyền theo vai trò:** 6 roles với quyền hạn khác nhau
- **Lưu trữ và quản lý file:** Upload, lưu trữ, và quản lý file đính kèm đề cương
- **Tìm kiếm công khai:** Cho phép sinh viên và công chúng tìm kiếm đề cương đã xuất bản

### 1.2. Đối tượng sử dụng

- **Lecturer (Giảng viên):** Tạo, chỉnh sửa, và nộp đề cương
- **HoD (Trưởng khoa):** Duyệt đề cương cấp khoa
- **AA (Phòng Đào tạo):** Duyệt đề cương cấp phòng
- **Principal (Hiệu trưởng):** Xuất bản đề cương
- **Admin (Quản trị viên):** Quản lý người dùng và hệ thống
- **Student (Sinh viên):** Xem đề cương đã xuất bản

---

## 2. Tech Stack

### 2.1. Backend

- **Framework:** Flask 2.0+ (Python)
- **Architecture:** Clean Architecture (API, Domain, Infrastructure, Services layers)
- **ORM:** SQLAlchemy 1.4+
- **Database:** Microsoft SQL Server (MSSQL) - Primary database
- **File Storage:** Supabase Storage (PostgreSQL-based object storage)
- **Authentication:** JWT (JSON Web Tokens)
- **API Documentation:** OpenAPI 3.0 (Swagger UI)
- **Validation:** Marshmallow schemas
- **Dependency Injection:** Custom dependency container

### 2.2. Frontend

- **Framework:** React 18
- **Build Tool:** Vite
- **Language:** TypeScript
- **Styling:** TailwindCSS
- **Routing:** React Router v6
- **Form Management:** react-hook-form + zod
- **State Management:** Context API + useReducer
- **HTTP Client:** Fetch API (custom apiClient wrapper)

### 2.3. Database

- **Primary:** Microsoft SQL Server (MSSQL)
  - Lưu trữ tất cả business data
  - Models: User, Role, Syllabus, SyllabusVersion, FileAsset, etc.
- **Storage:** Supabase Storage (PostgreSQL-based)
  - Lưu trữ file đính kèm (PDF, DOCX)
  - Metadata lưu trong MSSQL (FileAsset table)

---

## 3. Project Status

### ✅ COMPLETE & RUNNABLE

Hệ thống đã hoàn thiện và sẵn sàng cho demo:

- ✅ **Backend:** Running và stable
- ✅ **Frontend:** Builds successfully, runs cleanly
- ✅ **Integration:** FE-BE connected và working
- ✅ **UI:** Modern, academic, professional
- ✅ **Code Quality:** Clean, no errors, well-structured
- ✅ **Documentation:** API documentation (Swagger UI)
- ✅ **File Storage:** Supabase Storage integration complete
- ✅ **Authorization:** RBAC implemented với 6 roles
- ✅ **Workflow:** Full workflow từ DRAFT đến PUBLISHED

### Key Features Implemented

1. **Authentication & Authorization:**
   - JWT-based authentication
   - Role-based access control (6 roles)
   - Token expiration (2 hours)

2. **Syllabus Management:**
   - Create, read, update syllabus
   - Workflow transitions (DRAFT → PENDING_REVIEW → PENDING_APPROVAL → APPROVED → PUBLISHED)
   - Version management

3. **File Management:**
   - Upload PDF/DOCX files (max 20MB)
   - Rename, replace, delete files
   - Signed URL for secure download
   - Supabase Storage integration

4. **User Management (Admin):**
   - CRUD operations
   - Role assignment
   - User status management

5. **Public Access:**
   - Search published syllabi
   - View published syllabus details

---

## 4. Cấu trúc Thư mục

```
CNPM_SMD/
├── backend/              # Backend Flask API
│   ├── src/
│   │   ├── api/          # API layer
│   │   │   ├── controllers/  # 8 controllers (auth, user, syllabus, file, admin, public, subject, program)
│   │   │   ├── schemas/      # Marshmallow schemas
│   │   │   ├── utils/       # authz.py, db.py
│   │   │   ├── middleware.py
│   │   │   ├── responses.py
│   │   │   ├── routes.py
│   │   │   └── swagger.py
│   │   ├── domain/       # Domain layer (business logic)
│   │   │   ├── constants.py
│   │   │   ├── exceptions.py
│   │   │   ├── models/      # Domain models
│   │   │   └── services/    # password_hasher, auth_service
│   │   ├── infrastructure/  # Infrastructure layer
│   │   │   ├── databases/   # mssql.py, base.py, postgresql.py
│   │   │   ├── models/       # 25+ SQLAlchemy models
│   │   │   ├── repositories/ # Repository implementations
│   │   │   └── services/     # supabase_storage.py
│   │   ├── services/     # Application services
│   │   │   ├── user_service.py
│   │   │   ├── syllabus_service.py
│   │   │   ├── file_service.py
│   │   │   └── authz/         # Authorization policies
│   │   ├── scripts/      # Database scripts
│   │   ├── app.py        # Flask app entry point
│   │   ├── config.py     # Configuration
│   │   └── requirements.txt
│   └── docs/             # Backend documentation
│
├── frontend/             # Frontend React App
│   ├── src/
│   │   ├── app/          # App config
│   │   │   ├── router.tsx
│   │   │   └── store/    # authContext, notificationContext
│   │   ├── components/   # Reusable components
│   │   │   ├── ui/       # Button, Input, Table, Modal, etc.
│   │   │   ├── workflow/ # StatusBadge, WorkflowTimeline
│   │   │   └── syllabi/  # VersionAttachments
│   │   ├── features/     # Feature pages
│   │   │   ├── auth/
│   │   │   ├── dashboard/
│   │   │   ├── syllabi/
│   │   │   ├── users/
│   │   │   ├── hod/
│   │   │   ├── aa/
│   │   │   ├── principal/
│   │   │   ├── admin/
│   │   │   └── student/
│   │   ├── services/     # API services
│   │   ├── types/        # TypeScript types
│   │   └── utils/        # Utilities
│   ├── package.json
│   └── README.md
│
├── docs/                 # Tài liệu chuẩn (đồ án)
│   ├── 00_overview.md
│   ├── 01_requirements.md
│   ├── 02_architecture.md
│   ├── ...
│   └── README.md
│
└── README.md            # Entry point (hướng dẫn setup)
```

---

## 5. Workflow Overview

### 5.1. Workflow States

```
DRAFT → PENDING_REVIEW → PENDING_APPROVAL → APPROVED → PUBLISHED
```

**Mô tả:**
- **DRAFT:** Giảng viên đang soạn thảo
- **PENDING_REVIEW:** Đã nộp, chờ Trưởng khoa duyệt
- **PENDING_APPROVAL:** Đã duyệt khoa, chờ Phòng Đào tạo duyệt
- **APPROVED:** Đã duyệt, chờ Hiệu trưởng xuất bản
- **PUBLISHED:** Đã xuất bản, công khai

### 5.2. Role Permissions

| Role | Create | Edit | Submit | Review | Approve | Publish | View Published |
|------|--------|------|--------|--------|---------|---------|----------------|
| **Lecturer** | ✅ | ✅ (own, DRAFT) | ✅ (own, DRAFT) | ❌ | ❌ | ❌ | ✅ |
| **HoD** | ❌ | ❌ | ❌ | ✅ | ✅ (level 1) | ❌ | ✅ |
| **AA** | ❌ | ❌ | ❌ | ✅ | ✅ (level 2) | ❌ | ✅ |
| **Principal** | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| **Admin** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Student** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ (published only) |

---

## 6. Key Components

### 6.1. Backend Components

- **Controllers:** Xử lý HTTP requests/responses
- **Services:** Business logic và transaction management
- **Repositories:** Data access layer (abstraction)
- **Models:** Domain models và Infrastructure models
- **Policies:** Authorization policies (file_access, file_mutation)

### 6.2. Frontend Components

- **Pages:** Feature-based pages (Lecturer, HoD, AA, Principal, Admin, Student)
- **Components:** Reusable UI components
- **Services:** API client services
- **Guards:** Route guards (ProtectedRoute, RoleGuard variants)
- **Context:** Global state (Auth, Notifications)

---

## 7. API Overview

### Base URL
- **Development:** `http://localhost:9999`
- **API Documentation:** `http://localhost:9999/docs` (Swagger UI)

### Main Endpoints

- **Auth:** `/auth/login`, `/auth/me`
- **Users:** `/users` (CRUD)
- **Syllabi:** `/syllabi` (CRUD, workflow actions)
- **Files:** `/files` (upload, download, signed-url, mutations)
- **Admin:** `/admin/users`, `/admin/roles`, `/admin/publishing`
- **Public:** `/public/syllabi` (search, view published)

### Response Format

Tất cả endpoints trả về format chuẩn:

```json
{
  "success": true,
  "data": { ... },
  "message": "Operation successful"
}
```

Hoặc error:

```json
{
  "success": false,
  "message": "Error message",
  "errors": { ... }  // Optional, for validation errors
}
```

---

## 8. Security

- **Authentication:** JWT tokens (2-hour expiration)
- **Authorization:** Role-based access control (RBAC)
- **Password:** Bcrypt hashing
- **File Storage:** Private bucket với signed URLs
- **CORS:** Configured cho development origins
- **Input Validation:** Marshmallow schemas (backend), zod (frontend)

---

## 9. Development Environment

### Prerequisites

- Python 3.8+
- Node.js 18+
- Docker (cho MSSQL Server)
- Supabase (local hoặc cloud, cho file storage)

### Quick Start

Xem [09_deployment.md](09_deployment.md) để biết chi tiết setup.

---

## 10. Tài liệu Tham khảo

- **Kiến trúc:** [02_architecture.md](02_architecture.md)
- **Workflow:** [04_workflow.md](04_workflow.md)
- **Backend Design:** [05_backend_design.md](05_backend_design.md)
- **Frontend Design:** [06_frontend_design.md](06_frontend_design.md)
- **File Storage:** [07_file_storage_supabase.md](07_file_storage_supabase.md)
- **Deployment:** [09_deployment.md](09_deployment.md)

---

**Hệ thống SMD đã sẵn sàng cho demo và đánh giá đồ án CNPM.**
