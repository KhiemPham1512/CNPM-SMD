# Yêu cầu Hệ thống

---

## 1. Functional Requirements

### 1.1. Quản lý Người dùng

**FR1.1 - Authentication:**
- Hệ thống phải hỗ trợ đăng nhập bằng username/password
- Token JWT được sử dụng cho authentication
- Token có thời gian hết hạn (2 giờ)

**FR1.2 - Role Management:**
- Hệ thống hỗ trợ 6 roles:
  - ADMIN: Quản trị hệ thống
  - LECTURER: Giảng viên
  - HOD: Trưởng khoa
  - AA: Phòng Đào tạo
  - PRINCIPAL: Hiệu trưởng
  - STUDENT: Sinh viên
- Mỗi user có thể có nhiều roles
- Admin có thể assign/remove roles cho users

### 1.2. Quản lý Đề cương

**FR2.1 - Create Syllabus:**
- Chỉ LECTURER có thể tạo đề cương draft
- Phải chọn Subject và Program từ danh sách
- Owner được tự động set từ user đăng nhập
- Tạo đề cương sẽ tự động tạo version đầu tiên (DRAFT)

**FR2.2 - Edit Syllabus:**
- Chỉ owner (LECTURER) có thể edit đề cương ở trạng thái DRAFT
- Có thể thay đổi Subject và Program
- Owner không thể thay đổi

**FR2.3 - View Syllabus:**
- Tất cả authenticated users có thể xem đề cương
- STUDENT chỉ xem được đề cương đã PUBLISHED
- Các roles khác xem được theo quyền workflow

**FR2.4 - List Syllabi:**
- LECTURER có thể filter "My Syllabi Only" (chỉ đề cương của mình)
- Có thể search theo ID, Subject ID, Program ID
- Có thể filter theo status

### 1.3. Workflow Management

**FR3.1 - Workflow States:**
- DRAFT: Đang soạn thảo (Lecturer -Giảng viên)
- PENDING_REVIEW: Chờ Trưởng khoa duyệt
- PENDING_APPROVAL: Chờ Phòng Đào tạo duyệt
- APPROVED: Đã duyệt, chờ xuất bản
- PUBLISHED: Đã xuất bản

**FR3.2 - Submit for Review:**
- LECTURER (owner) có thể submit đề cương DRAFT
- Submit chuyển status sang PENDING_REVIEW
- Sau khi submit, không thể edit nữa

**FR3.3 - HoD Review:**
- HoD có thể xem danh sách đề cương PENDING_REVIEW
- HoD có thể approve hoặc reject
- Approve: chuyển sang PENDING_APPROVAL
- Reject: chuyển về DRAFT (có thể kèm lý do)

**FR3.4 - AA Review:**
- AA có thể xem danh sách đề cương PENDING_APPROVAL
- AA có thể approve hoặc reject
- Approve: chuyển sang APPROVED
- Reject: chuyển về DRAFT (có thể kèm lý do)

**FR3.5 - Principal Publish:**
- Principal có thể xem danh sách đề cương APPROVED
- Principal có thể publish hoặc unpublish
- Publish: chuyển sang PUBLISHED (công khai)
- Unpublish: chuyển về APPROVED (không công khai)

### 1.4. File Management

**FR4.1 - Upload File:**
- Chỉ LECTURER (owner) có thể upload file khi status = DRAFT
- File types: PDF, DOCX, DOC
- File size limit: 20MB
- File được lưu trong Supabase Storage
- Metadata lưu trong database (FileAsset table)

**FR4.2 - File Operations:**
- Rename display_name (chỉ DRAFT + owner)
- Replace file content (chỉ DRAFT + owner)
- Delete file (chỉ DRAFT + owner)
- Download file (signed URL, có expiration)

**FR4.3 - File List:**
- Hiển thị danh sách files của một version
- Hiển thị: filename, type, size, uploaded date
- Download button cho mỗi file

### 1.5. Public Access

**FR5.1 - Search Published Syllabi:**
- Student và Public có thể search đề cương đã PUBLISHED
- Search theo keyword (tên đề cương, subject, program)

**FR5.2 - View Published Syllabus:**
- Student và Public có thể xem chi tiết đề cương đã PUBLISHED
- Không thể xem workflow status hoặc internal information

### 1.6. Admin Functions

**FR6.1 - User Management:**
- Admin có thể CRUD users
- Admin có thể assign/remove roles
- Admin có thể lock/unlock users

**FR6.2 - System Settings:**
- Admin có thể quản lý system settings
- Admin có thể quản lý publishing (unpublish, archive)

---

## 2. Non-Functional Requirements

### 2.1. Performance

- **Response Time:** API response < 500ms cho các operations thông thường
- **File Upload:** Upload file < 20MB trong < 30 giây
- **Concurrent Users:** Hỗ trợ ít nhất 50 concurrent users

### 2.2. Security

- **Authentication:** JWT tokens với expiration
- **Authorization:** Role-based access control (RBAC)
- **Password:** Bcrypt hashing (không lưu plain text)
- **File Storage:** Private bucket với signed URLs (có expiration)
- **Input Validation:** Validate tất cả inputs (backend + frontend)
- **Error Messages:** Không leak sensitive information trong production

### 2.3. Scalability

- **Database:** MSSQL có thể scale với indexes
- **File Storage:** Supabase Storage có thể scale
- **Architecture:** Clean Architecture cho dễ maintain và extend

### 2.4. Usability

- **UI:** Modern, clean, academic theme
- **Responsive:** Hoạt động tốt trên desktop
- **Error Handling:** Clear error messages
- **Loading States:** Hiển thị loading indicators
- **Form Validation:** Real-time validation với clear messages

### 2.5. Maintainability

- **Code Quality:** Clean code, well-structured
- **Documentation:** API documentation (Swagger), code comments
- **Testing:** Manual test checklist
- **Error Logging:** Comprehensive logging

### 2.6. Compatibility

- **Backend:** Python 3.8+, Flask 2.0+
- **Frontend:** Node.js 18+, React 18, modern browsers
- **Database:** MSSQL Server 2019+
- **Storage:** Supabase Storage (PostgreSQL-based)

---

## 3. Use Cases

### 3.1. Lecturer Use Cases

1. **UC-L1:** Tạo đề cương draft
2. **UC-L2:** Chỉnh sửa đề cương draft
3. **UC-L3:** Upload file đính kèm
4. **UC-L4:** Submit đề cương để duyệt
5. **UC-L5:** Xem danh sách đề cương của mình
6. **UC-L6:** Xem chi tiết đề cương

### 3.2. HoD Use Cases

1. **UC-H1:** Xem danh sách đề cương chờ duyệt (PENDING_REVIEW)
2. **UC-H2:** Xem chi tiết đề cương chờ duyệt
3. **UC-H3:** Approve đề cương (chuyển sang PENDING_APPROVAL)
4. **UC-H4:** Reject đề cương (chuyển về DRAFT, kèm lý do)

### 3.3. AA Use Cases

1. **UC-A1:** Xem danh sách đề cương chờ duyệt (PENDING_APPROVAL)
2. **UC-A2:** Xem chi tiết đề cương chờ duyệt
3. **UC-A3:** Approve đề cương (chuyển sang APPROVED)
4. **UC-A4:** Reject đề cương (chuyển về DRAFT, kèm lý do)

### 3.4. Principal Use Cases

1. **UC-P1:** Xem danh sách đề cương đã duyệt (APPROVED)
2. **UC-P2:** Xem chi tiết đề cương
3. **UC-P3:** Publish đề cương (chuyển sang PUBLISHED)
4. **UC-P4:** Unpublish đề cương (chuyển về APPROVED)

### 3.5. Admin Use Cases

1. **UC-AD1:** Quản lý users (CRUD)
2. **UC-AD2:** Assign/remove roles cho users
3. **UC-AD3:** Lock/unlock users
4. **UC-AD4:** Quản lý system settings
5. **UC-AD5:** Quản lý publishing (unpublish, archive)

### 3.6. Student/Public Use Cases

1. **UC-S1:** Search đề cương đã published
2. **UC-S2:** Xem chi tiết đề cương đã published
3. **UC-S3:** Download file đính kèm (nếu có)

---

## 4. Constraints

### 4.1. Technical Constraints

- **Database:** Phải dùng MSSQL (yêu cầu đồ án)
- **File Storage:** Supabase Storage (optional, có thể disable)
- **Backend:** Flask (Python)
- **Frontend:** React (TypeScript)

### 4.2. Business Constraints

- **Workflow:** Phải tuân theo quy trình: DRAFT → PENDING_REVIEW → PENDING_APPROVAL → APPROVED → PUBLISHED
- **Authorization:** Chỉ owner mới có thể edit đề cương DRAFT
- **File Upload:** Chỉ cho phép PDF, DOCX, DOC (max 20MB)

### 4.3. Development Constraints

- **Scope:** Đồ án CNPM - demo system
- **Time:** Limited development time
- **Resources:** Local development environment

---

## 5. Assumptions

1. **Database:** MSSQL Server đã được setup (Docker hoặc local)
2. **Supabase:** Supabase Storage là optional (có thể disable)
3. **Network:** Backend và Frontend chạy trên cùng localhost
4. **Users:** Demo users được seed sẵn
5. **Data:** Demo data (subjects, programs) được seed sẵn

---

**Tài liệu này mô tả các yêu cầu chức năng và phi chức năng của hệ thống SMD.**
