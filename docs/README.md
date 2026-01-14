# SMD - Tài liệu Hệ thống

**Hệ thống Quản lý và Số hóa Đề cương Học phần (Syllabus Management & Digitization System)**

---

## 📚 Giới thiệu

Đây là bộ tài liệu đầy đủ cho đồ án CNPM - Hệ thống SMD. Tài liệu được tổ chức theo cấu trúc chuẩn, phù hợp cho việc chấm đồ án và tham khảo.

---

## 📖 Cấu trúc Tài liệu

### 00. [Tổng quan Hệ thống](00_overview.md)
- Giới thiệu hệ thống SMD
- Mục tiêu đồ án
- Tech stack
- Project status
- Cấu trúc thư mục

### 01. [Yêu cầu Hệ thống](01_requirements.md)
- Functional requirements
- Non-functional requirements
- Use cases theo role

### 02. [Kiến trúc Hệ thống](02_architecture.md)
- Clean Architecture principles
- Layer structure (API, Domain, Infrastructure, Services)
- Tech stack chi tiết
- Dependency injection
- Repository pattern

### 03. [Thiết kế Cơ sở Dữ liệu](03_database_design.md)
- ERD và relationships
- Tables và columns
- Foreign keys
- Migration strategy

### 04. [Workflow và Kịch bản](04_workflow.md)
- Workflow states (DRAFT → PUBLISHED)
- Kịch bản theo từng role:
  - Lecturer: Create → Edit → Upload → Submit
  - HoD: Review → Approve/Reject
  - AA: Review → Approve/Reject
  - Principal: Publish/Unpublish
  - Admin: User management
  - Student/Public: View published

### 05. [Thiết kế Backend](05_backend_design.md)
- API endpoints (RESTful)
- Authentication (JWT)
- Authorization (RBAC)
- Response format
- Error handling
- Swagger documentation

### 06. [Thiết kế Frontend](06_frontend_design.md)
- Tech stack (React, TypeScript, Vite)
- Component structure
- Routing
- Role-based UI
- State management
- Form validation

### 07. [File Storage & Supabase](07_file_storage_supabase.md)
- Supabase Storage integration
- File upload flow
- Signed URL generation
- File mutations (upload, rename, replace, delete)
- Setup guide
- Troubleshooting

### 08. [AI Module](08_ai_module.md)
- AI microservice overview (nếu có)
- AI summary generation
- Integration với workflow

### 09. [Triển khai & Deployment](09_deployment.md)
- Setup hướng dẫn
- Environment variables
- Database setup
- Running application
- Troubleshooting

### 10. [Testing & Verification](10_testing.md)
- Test plan
- Manual test checklist
- Verified findings
- Test scenarios

---

## 🚀 Quick Start

**Để bắt đầu nhanh, xem:**
- [00_overview.md](00_overview.md) - Tổng quan hệ thống
- [09_deployment.md](09_deployment.md) - Hướng dẫn chạy ứng dụng

**Để hiểu kiến trúc, xem:**
- [02_architecture.md](02_architecture.md) - Kiến trúc hệ thống
- [05_backend_design.md](05_backend_design.md) - Backend design
- [06_frontend_design.md](06_frontend_design.md) - Frontend design

**Để hiểu workflow, xem:**
- [04_workflow.md](04_workflow.md) - Workflow và kịch bản

**Để setup file storage, xem:**
- [07_file_storage_supabase.md](07_file_storage_supabase.md) - Supabase setup

---

## 📝 Ghi chú

- Tất cả tài liệu được viết bằng tiếng Việt (phù hợp đồ án CNPM)
- Code examples và technical terms giữ nguyên tiếng Anh
- Tài liệu được cập nhật theo codebase thực tế

---

**Chúc bạn đọc tài liệu hiệu quả! 📚**
