# Thiết kế Cơ sở Dữ liệu

---

## 1. Database Overview

**Primary Database:** Microsoft SQL Server (MSSQL)  
**Storage Database:** PostgreSQL (Supabase Storage - chỉ cho file storage)

### 1.1. Database Schema

Hệ thống sử dụng **25+ tables** để quản lý:
- Users và Roles
- Syllabi và Versions
- Subjects, Programs, Departments
- Files và Attachments
- Workflow và Reviews
- Notifications và Feedback

---

## 2. Core Tables

### 2.1. User Management

#### `user`
**Purpose:** Lưu thông tin người dùng

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `user_id` | INT | PK, Identity | Primary key |
| `username` | VARCHAR(255) | NOT NULL, UNIQUE | Username để login |
| `password_hash` | VARCHAR(255) | NOT NULL | Bcrypt hash |
| `full_name` | VARCHAR(255) | NOT NULL | Tên đầy đủ |
| `email` | VARCHAR(255) | NOT NULL | Email |
| `status` | VARCHAR(50) | NOT NULL | ACTIVE, LOCKED, etc. |
| `created_at` | DATETIME | NOT NULL | Ngày tạo |

**Relationships:**
- One-to-Many: `user_roles` (UserRole)
- One-to-Many: `syllabus_owner` (Syllabus)
- One-to-Many: `uploaded_files` (FileAsset)

#### `role`
**Purpose:** Định nghĩa các roles trong hệ thống

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `role_id` | INT | PK, Identity | Primary key |
| `role_name` | VARCHAR(255) | NOT NULL, UNIQUE | ADMIN, LECTURER, HOD, AA, PRINCIPAL, STUDENT |

**Relationships:**
- Many-to-Many: `user_roles` (UserRole)
- Many-to-Many: `role_permissions` (RolePermission)

#### `user_role`
**Purpose:** Junction table (User ↔ Role)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `user_id` | INT | PK, FK → user | User ID |
| `role_id` | INT | PK, FK → role | Role ID |

#### `permission`
**Purpose:** Định nghĩa permissions

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `permission_id` | INT | PK, Identity | Primary key |
| `code` | VARCHAR(255) | NOT NULL, UNIQUE | Permission code |
| `name` | VARCHAR(255) | NOT NULL | Permission name |
| `description` | VARCHAR(500) | NULL | Mô tả |

#### `role_permission`
**Purpose:** Junction table (Role ↔ Permission)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `role_id` | INT | PK, FK → role | Role ID |
| `permission_id` | INT | PK, FK → permission | Permission ID |

---

### 2.2. Syllabus Management

#### `syllabus`
**Purpose:** Lưu thông tin đề cương

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `syllabus_id` | INT | PK, Identity | Primary key |
| `subject_id` | INT | NOT NULL, FK → subject | Subject ID |
| `program_id` | INT | NOT NULL, FK → program | Program ID |
| `owner_lecturer_id` | INT | NOT NULL, FK → user | Owner (Lecturer) ID |
| `current_version_id` | INT | NULL, FK → syllabus_version | Current version ID |
| `lifecycle_status` | VARCHAR(50) | NOT NULL | DRAFT, PENDING_REVIEW, PENDING_APPROVAL, APPROVED, PUBLISHED |
| `created_at` | DATETIME | NOT NULL | Ngày tạo |

**Relationships:**
- Many-to-One: `subject` (Subject)
- Many-to-One: `program` (Program)
- Many-to-One: `owner` (User)
- One-to-One: `current_version` (SyllabusVersion)
- One-to-Many: `versions` (SyllabusVersion)

#### `syllabus_version`
**Purpose:** Lưu các version của đề cương

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `version_id` | INT | PK, Identity | Primary key |
| `syllabus_id` | INT | NOT NULL, FK → syllabus | Syllabus ID |
| `academic_year` | VARCHAR(20) | NOT NULL | Năm học |
| `version_no` | INT | NOT NULL | Số version |
| `workflow_status` | VARCHAR(50) | NOT NULL | DRAFT, PENDING_REVIEW, etc. |
| `submitted_at` | DATETIME | NULL | Ngày submit |
| `approved_at` | DATETIME | NULL | Ngày approve |
| `published_at` | DATETIME | NULL | Ngày publish |
| `created_by` | INT | NOT NULL, FK → user | User tạo version |
| `created_at` | DATETIME | NOT NULL | Ngày tạo |

**Relationships:**
- Many-to-One: `syllabus` (Syllabus)
- Many-to-One: `creator` (User)
- One-to-Many: `file_assets` (FileAsset)
- One-to-Many: `workflow_actions` (WorkflowAction)
- One-to-Many: `review_rounds` (ReviewRound)

---

### 2.3. Subject & Program Management

#### `department`
**Purpose:** Lưu thông tin khoa

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `department_id` | INT | PK, Identity | Primary key |
| `code` | VARCHAR(50) | NOT NULL, UNIQUE | Mã khoa |
| `name` | VARCHAR(255) | NOT NULL | Tên khoa |

**Relationships:**
- One-to-Many: `subjects` (Subject)
- One-to-Many: `programs` (Program)

#### `subject`
**Purpose:** Lưu thông tin môn học

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `subject_id` | INT | PK, Identity | Primary key |
| `department_id` | INT | NOT NULL, FK → department | Department ID |
| `code` | VARCHAR(50) | NOT NULL, UNIQUE | Mã môn học |
| `name` | VARCHAR(255) | NOT NULL | Tên môn học |
| `credits` | INT | NOT NULL | Số tín chỉ |
| `status` | VARCHAR(50) | NOT NULL | ACTIVE, INACTIVE |

**Relationships:**
- Many-to-One: `department` (Department)
- One-to-Many: `syllabi` (Syllabus)

#### `program`
**Purpose:** Lưu thông tin chương trình đào tạo

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `program_id` | INT | PK, Identity | Primary key |
| `department_id` | INT | NOT NULL, FK → department | Department ID |
| `code` | VARCHAR(50) | NOT NULL, UNIQUE | Mã chương trình |
| `name` | VARCHAR(255) | NOT NULL | Tên chương trình |

**Relationships:**
- Many-to-One: `department` (Department)
- One-to-Many: `syllabi` (Syllabus)

---

### 2.4. File Management

#### `file_asset`
**Purpose:** Lưu metadata của file đính kèm

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `file_id` | INT | PK, Identity | Primary key |
| `syllabus_version_id` | INT | NOT NULL, FK → syllabus_version | Version ID |
| `original_filename` | VARCHAR(255) | NOT NULL | Tên file gốc |
| `display_name` | VARCHAR(255) | NULL | Tên hiển thị (có thể rename) |
| `bucket` | VARCHAR(100) | NOT NULL | Supabase bucket name |
| `object_path` | VARCHAR(500) | NOT NULL | Path trong Supabase Storage |
| `mime_type` | VARCHAR(100) | NOT NULL | MIME type |
| `size_bytes` | INT | NOT NULL | Kích thước file (bytes) |
| `uploaded_by` | INT | NOT NULL, FK → user | User upload |
| `created_at` | DATETIME | NOT NULL | Ngày upload |

**Relationships:**
- Many-to-One: `version` (SyllabusVersion)
- Many-to-One: `uploader` (User)

**Note:** File thực tế lưu trong Supabase Storage, chỉ metadata lưu trong MSSQL.

---

### 2.5. Workflow Management

#### `workflow_action`
**Purpose:** Lưu lịch sử workflow actions (audit trail)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `action_id` | INT | PK, Identity | Primary key |
| `version_id` | INT | NOT NULL, FK → syllabus_version | Version ID |
| `actor_user_id` | INT | NOT NULL, FK → user | User thực hiện action |
| `action_type` | VARCHAR(50) | NOT NULL | submit, approve, reject, publish, unpublish |
| `action_note` | VARCHAR(1000) | NULL | Ghi chú (lý do reject, etc.) |
| `action_at` | DATETIME | NOT NULL | Thời gian action |

**Relationships:**
- Many-to-One: `version` (SyllabusVersion)
- Many-to-One: `actor` (User)

#### `review_round`
**Purpose:** Lưu thông tin vòng review

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `round_id` | INT | PK, Identity | Primary key |
| `version_id` | INT | NOT NULL, FK → syllabus_version | Version ID |
| `level` | VARCHAR(50) | NOT NULL | HOD, AA |
| `start_at` | DATETIME | NOT NULL | Bắt đầu review |
| `end_at` | DATETIME | NOT NULL | Kết thúc review |
| `created_by` | INT | NOT NULL, FK → user | User tạo round |

**Relationships:**
- Many-to-One: `version` (SyllabusVersion)
- Many-to-One: `creator` (User)
- One-to-Many: `review_comments` (ReviewComment)

#### `review_comment`
**Purpose:** Lưu comments trong quá trình review

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `comment_id` | INT | PK, Identity | Primary key |
| `round_id` | INT | NOT NULL, FK → review_round | Round ID |
| `version_id` | INT | NOT NULL, FK → syllabus_version | Version ID |
| `author_user_id` | INT | NOT NULL, FK → user | User viết comment |
| `target_section_id` | INT | NULL, FK → syllabus_section | Section được comment |
| `comment_text` | VARCHAR(2000) | NOT NULL | Nội dung comment |
| `created_at` | DATETIME | NOT NULL | Ngày tạo |
| `updated_at` | DATETIME | NOT NULL | Ngày cập nhật |
| `is_resolved` | BIT | NOT NULL | Đã resolve chưa |

**Relationships:**
- Many-to-One: `round` (ReviewRound)
- Many-to-One: `version` (SyllabusVersion)
- Many-to-One: `author` (User)
- Many-to-One: `target_section` (SyllabusSection)

---

### 2.6. Other Tables

- `syllabus_section`: Sections của đề cương
- `clo`, `plo`: Learning outcomes
- `clo_plo_map`: Mapping CLO-PLO
- `assessment_item`: Assessment items
- `subscription`: User subscriptions
- `feedback`: User feedback
- `notification`: Notifications
- `ai_job`, `ai_summary`: AI-related (nếu có)
- `audit_log`: Audit logs
- `system_setting`: System settings

---

## 3. Relationships

### 3.1. Core Relationships

```
User ←→ Role (Many-to-Many via UserRole)
User → Syllabus (One-to-Many: owner)
User → SyllabusVersion (One-to-Many: created_by)
User → FileAsset (One-to-Many: uploaded_by)

Syllabus → Subject (Many-to-One)
Syllabus → Program (Many-to-One)
Syllabus → SyllabusVersion (One-to-Many)
Syllabus → SyllabusVersion (One-to-One: current_version)

SyllabusVersion → FileAsset (One-to-Many)
SyllabusVersion → WorkflowAction (One-to-Many)
SyllabusVersion → ReviewRound (One-to-Many)

Subject → Department (Many-to-One)
Program → Department (Many-to-One)
```

### 3.2. ERD (Text-based)

```
┌──────────┐         ┌──────────────┐         ┌──────────┐
│  User    │─────────│  UserRole    │─────────│  Role    │
└──────────┘         └──────────────┘         └──────────┘
     │
     │ (owner)
     │
     ▼
┌──────────┐         ┌──────────────────┐
│ Syllabus │─────────│ SyllabusVersion  │
└──────────┘         └──────────────────┘
     │                       │
     │ (subject)             │ (files)
     │                       │
     ▼                       ▼
┌──────────┐         ┌──────────────┐
│ Subject  │         │  FileAsset  │
└──────────┘         └──────────────┘
     │
     │ (department)
     │
     ▼
┌──────────┐
│Department│
└──────────┘
```

---

## 4. Migration Strategy

### 4.1. Current Approach

**Development/Demo:**
- Sử dụng `AUTO_CREATE_TABLES=True` trong `.env`
- `Base.metadata.create_all()` tạo tables tự động
- Script `scripts/reset_db.py` để rebuild database

**Production (Recommended):**
- Sử dụng migration tool (Alembic) - TODO
- Versioned migrations
- Không dùng `create_all()` trong production

### 4.2. Table Creation

**Script:** `scripts/reset_db.py`

```python
# Recreate all tables
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
```

**Seed Data:** `scripts/seed_mvp.py`
- Tạo 6 roles
- Tạo 6 demo users
- Tạo demo data (departments, programs, subjects)

---

## 5. Indexes

**Current:** Primary keys và Foreign keys tự động có indexes.

**Recommended (Future):**
- Index trên `syllabus.lifecycle_status` (cho filtering)
- Index trên `syllabus_version.workflow_status` (cho filtering)
- Index trên `file_asset.syllabus_version_id` (cho queries)
- Index trên `user.username` (cho login lookup)

---

## 6. Data Integrity

### 6.1. Foreign Key Constraints

Tất cả foreign keys đều có constraints:
- `ON DELETE RESTRICT` (default)
- Không cho phép xóa parent nếu có child records

### 6.2. Unique Constraints

- `user.username` - UNIQUE
- `role.role_name` - UNIQUE
- `subject.code` - UNIQUE
- `program.code` - UNIQUE
- `department.code` - UNIQUE

### 6.3. Check Constraints

- `syllabus.lifecycle_status` - Must be valid workflow state
- `syllabus_version.workflow_status` - Must be valid workflow state
- `file_asset.size_bytes` - Must be > 0

---

## 7. Database Connection

**Connection String Format:**
```
mssql+pymssql://[username]:[password]@[host]:[port]/[database]
```

**Example:**
```
mssql+pymssql://sa:Aa%40123456@127.0.0.1:1433/smd
```

**Note:** Password phải được URL encode (`@` → `%40`)

---

## 8. Supabase Storage (PostgreSQL)

**Purpose:** Chỉ dùng cho file storage, không lưu business data.

**Tables (Supabase):**
- `storage.objects` - File objects trong buckets
- `storage.buckets` - Bucket definitions

**Metadata (MSSQL):**
- `file_asset` table lưu metadata (bucket, object_path, etc.)

---

**Database design đảm bảo data integrity và hỗ trợ đầy đủ workflow của hệ thống.**
