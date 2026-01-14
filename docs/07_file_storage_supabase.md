# File Storage & Supabase Integration

---

## 1. Overview

Hệ thống SMD sử dụng **Supabase Storage** để lưu trữ file đính kèm đề cương (PDF, DOCX, DOC). Metadata của file được lưu trong MSSQL (`file_asset` table), còn file thực tế lưu trong Supabase Storage.

### 1.1. Architecture

```
Frontend → Backend API → Supabase Storage
              ↓
           MSSQL (metadata)
```

**Flow:**
1. Frontend upload file → Backend API
2. Backend upload file → Supabase Storage
3. Backend lưu metadata → MSSQL (FileAsset table)
4. Backend trả về file_id và metadata
5. Frontend hiển thị file list

**Download:**
1. Frontend request signed URL → Backend API
2. Backend generate signed URL từ Supabase
3. Frontend download file từ signed URL

---

## 2. Integration Architecture

### 2.1. Backend Components

**Service Layer:**
- `infrastructure/services/supabase_storage.py` - SupabaseStorageService
  - `upload_file()` - Upload file to Supabase
  - `get_signed_url()` - Generate signed URL
  - `delete_file()` - Delete file from Supabase

**Service:**
- `services/file_service.py` - FileService
  - Orchestrates upload/download/delete
  - Handles transaction boundaries
  - Implements compensating delete (cleanup on error)

**Controller:**
- `api/controllers/file_controller.py` - File endpoints
  - `POST /files/upload` - Upload file
  - `GET /files/version/<version_id>` - List files
  - `GET /files/<file_id>/signed-url` - Get signed URL
  - `PATCH /files/<file_id>` - Rename file
  - `POST /files/<file_id>/replace` - Replace file
  - `DELETE /files/<file_id>` - Delete file
  - `GET /files/health` - Health check

**Model:**
- `infrastructure/models/file_asset.py` - FileAsset (SQLAlchemy)
  - Lưu metadata: bucket, object_path, mime_type, size_bytes, etc.

### 2.2. Frontend Components

**Service:**
- `services/fileService.ts` - FileService
  - `uploadFile()` - Upload với FormData
  - `getFilesByVersion()` - List files
  - `getSignedUrl()` - Get signed URL
  - `downloadFile()` - Download file
  - `renameFile()` - Rename display_name
  - `replaceFile()` - Replace file content
  - `deleteFile()` - Delete file
  - `checkHealth()` - Check storage status

**Component:**
- `components/syllabi/VersionAttachments.tsx` - UI component
  - Upload button (chỉ LECTURER, DRAFT, owner)
  - File list với download/rename/replace/delete
  - Health check integration

---

## 3. Upload Flow

### 3.1. Complete Flow

```
1. User selects file (PDF/DOCX/DOC, max 20MB)
   ↓
2. Frontend validates (type, size)
   ↓
3. Frontend calls fileService.uploadFile(versionId, file)
   ↓
4. Backend receives POST /files/upload
   - Validates FILE_STORAGE_ENABLED
   - Validates file type/size
   - Validates user role (LECTURER)
   - Validates version exists
   - Validates authorization (owner, DRAFT status)
   ↓
5. Backend uploads to Supabase Storage
   - Generates unique filename (UUID)
   - Path: syllabi/{syllabus_id}/versions/{version_id}/{uuid}.pdf
   ↓
6. Backend saves metadata to MSSQL
   - Creates FileAsset record
   - Commits transaction
   ↓
7. If DB fails → Cleanup Supabase file (retry 3 times)
   ↓
8. Backend returns file metadata
   ↓
9. Frontend refreshes file list
```

### 3.2. Error Handling

**If Supabase upload fails:**
- Return error immediately
- No cleanup needed (file not uploaded)

**If DB insert fails (after Supabase upload succeeds):**
- Retry delete from Supabase (3 attempts, exponential backoff)
- Log orphaned files if cleanup fails
- Return error to user

---

## 4. File Operations

### 4.1. Upload

**Endpoint:** `POST /files/upload`

**Request:**
- `file`: File object (multipart/form-data)
- `syllabus_version_id`: integer
- `display_name`: string (optional)

**Authorization:**
- Role: LECTURER only
- Owner: Must be owner of syllabus
- Status: Syllabus version must be DRAFT

**Response:**
```json
{
  "success": true,
  "data": {
    "file_id": 1,
    "syllabus_version_id": 1,
    "original_filename": "document.pdf",
    "display_name": "document.pdf",
    "bucket": "syllabus-files",
    "object_path": "syllabi/1/versions/1/uuid.pdf",
    "mime_type": "application/pdf",
    "size_bytes": 12345,
    "uploaded_by": 2,
    "created_at": "2024-01-01T00:00:00"
  }
}
```

### 4.2. List Files

**Endpoint:** `GET /files/version/<version_id>`

**Authorization:**
- Authenticated users can view
- Students only see published versions (404 for others)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "file_id": 1,
      "syllabus_version_id": 1,
      "original_filename": "document.pdf",
      "display_name": "document.pdf",
      ...
    }
  ]
}
```

### 4.3. Get Signed URL

**Endpoint:** `GET /files/<file_id>/signed-url?expires_in=3600`

**Authorization:**
- Authenticated users
- Students only for published versions

**Response:**
```json
{
  "success": true,
  "data": {
    "file_id": 1,
    "signed_url": "http://localhost:8000/storage/v1/object/sign/...",
    "expires_in": 3600,
    "object_path": "syllabi/1/versions/1/uuid.pdf"
  }
}
```

**Signed URL:**
- Expires after `expires_in` seconds (default: 3600 = 1 hour)
- Private bucket access
- No authentication required (signed URL is the auth)

### 4.4. Rename File

**Endpoint:** `PATCH /files/<file_id>`

**Request:**
```json
{
  "display_name": "New Name.pdf"
}
```

**Authorization:**
- Role: LECTURER
- Owner: Must be owner
- Status: DRAFT

### 4.5. Replace File

**Endpoint:** `POST /files/<file_id>/replace`

**Request:**
- `file`: New file (multipart/form-data)

**Authorization:**
- Role: LECTURER
- Owner: Must be owner
- Status: DRAFT

**Flow:**
1. Upload new file to Supabase
2. Delete old file from Supabase
3. Update metadata in DB
4. If DB fails → Cleanup new file

### 4.6. Delete File

**Endpoint:** `DELETE /files/<file_id>`

**Authorization:**
- Role: LECTURER
- Owner: Must be owner
- Status: DRAFT

**Flow:**
1. Delete from DB
2. Delete from Supabase (best-effort)

---

## 5. Setup Guide

### 5.1. Required Environment Variables

Thêm vào `backend/.env`:

```env
# Enable file storage
FILE_STORAGE_ENABLED=true

# Supabase Configuration
SUPABASE_URL=http://localhost:8000
# Hoặc nếu dùng Supabase cloud: https://your-project.supabase.co

SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
# Lấy từ Supabase dashboard hoặc .env của Supabase local

SUPABASE_BUCKET=syllabus-files
# Tên bucket (mặc định: syllabus-files)

SUPABASE_SIGNED_URL_EXPIRES_IN=3600
# Thời gian hết hạn signed URL (giây, mặc định: 3600 = 1 giờ)

MAX_UPLOAD_MB=20
# Giới hạn kích thước file upload (MB, mặc định: 20MB)
```

### 5.2. Lấy Supabase Credentials

**Local Supabase:**
```bash
# Chạy Supabase local
supabase start

# Lấy thông tin
supabase status

# SUPABASE_URL: API URL (thường là http://localhost:8000)
# SUPABASE_SERVICE_ROLE_KEY: Từ file .env trong thư mục Supabase
#   Thường ở: ~/.supabase/.env hoặc trong project supabase/.env
#   Key: SERVICE_ROLE_KEY
```

**Supabase Cloud:**
- `SUPABASE_URL`: Từ project settings → API URL
- `SUPABASE_SERVICE_ROLE_KEY`: Từ project settings → API → service_role key (secret)

### 5.3. Tạo Bucket `syllabus-files`

**Option A: Supabase Studio (Recommended)**

1. Mở Supabase Studio:
   - Local: http://localhost:3000
   - Cloud: https://app.supabase.com → chọn project → Storage

2. Tạo bucket:
   - Click "New bucket"
   - Name: `syllabus-files`
   - **Public bucket:** ❌ **UNCHECKED** (private bucket)
   - Click "Create bucket"

**Option B: Supabase CLI**

```bash
# Tạo bucket
supabase storage create syllabus-files --public false

# Verify
supabase storage list
```

### 5.4. Bucket Policy

**Lưu ý:** Vì backend dùng `SERVICE_ROLE_KEY`, nó có full access và bypass RLS. Signed URL sẽ hoạt động mà không cần policy phức tạp.

**Nếu muốn set policy cho an toàn hơn:**
1. Trong Supabase Studio → Storage → Policies
2. Tạo policy cho bucket `syllabus-files`:
   - **Policy name:** `Allow signed URL access`
   - **Allowed operation:** SELECT (read)
   - **Policy definition:**
     ```sql
     (bucket_id = 'syllabus-files'::text)
     ```
   - **Target roles:** `authenticated`, `anon`

---

## 6. Health Check

### 6.1. Endpoint

**GET /files/health** (public, không cần auth)

**Response:**
```json
{
  "success": true,
  "data": {
    "enabled": true,
    "configured": true,
    "provider": "supabase",
    "bucket": "syllabus-files"
  },
  "message": "File storage is enabled and configured"
}
```

**States:**
- `enabled: false` → File storage disabled
- `enabled: true, configured: false` → Missing env vars
- `enabled: true, configured: true` → Ready to use

### 6.2. Frontend Integration

Frontend gọi `/files/health` 1 lần khi component mount để quyết định render UI:
- Nếu `enabled=false` → Show "File storage is disabled"
- Nếu `configured=false` → Show "Storage enabled but not configured"
- Nếu `enabled=true, configured=true` → Load files như bình thường

---

## 7. Troubleshooting

### 7.1. Error: "File storage is disabled"

**Nguyên nhân:** `FILE_STORAGE_ENABLED=false` hoặc không set trong `.env`

**Fix:**
```env
FILE_STORAGE_ENABLED=true
```

**Restart backend** sau khi sửa.

### 7.2. Error: "Supabase configuration missing"

**Nguyên nhân:** Thiếu `SUPABASE_URL` hoặc `SUPABASE_SERVICE_ROLE_KEY`

**Fix:**
- Kiểm tra `.env` có đầy đủ:
  - `SUPABASE_URL`
  - `SUPABASE_SERVICE_ROLE_KEY`
  - `SUPABASE_BUCKET` (optional, default: syllabus-files)

**Restart backend** sau khi sửa.

### 7.3. Error: "Failed to upload file to Supabase"

**Nguyên nhân có thể:**
1. Supabase không chạy (local) hoặc URL sai
2. Service role key sai
3. Bucket chưa được tạo
4. Network issue

**Fix:**
1. Verify Supabase đang chạy: `supabase status` (local) hoặc check dashboard (cloud)
2. Verify bucket tồn tại: `supabase storage list` hoặc check Studio
3. Verify service role key đúng: copy từ Supabase `.env` hoặc dashboard

### 7.4. Error: "Supabase did not return a signed URL"

**Nguyên nhân:** Bucket policy hoặc RLS block access

**Fix:**
- Vì dùng service role key, nên bypass RLS
- Nếu vẫn lỗi, check bucket có tồn tại và service role key có quyền

### 7.5. Health check trả `configured: false`

**Nguyên nhân:** Thiếu một trong các env vars: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_BUCKET`

**Fix:**
- Check `.env` có đầy đủ các biến
- Restart backend server sau khi sửa `.env`

---

## 8. Security

### 8.1. Service Role Key

- ⚠️ **KHÔNG BAO GIỜ** expose service role key ở frontend
- Chỉ dùng ở backend
- Service role key bypass RLS → có full access

### 8.2. Bucket Policy

- Bucket nên là **private** (không public)
- Dùng signed URL để download (có expiration)
- Backend validate user permissions trước khi generate signed URL

### 8.3. File Validation

- Backend validate file type (PDF/DOCX/DOC)
- Backend validate file size (max 20MB default)
- Backend validate user role (chỉ LECTURER có thể upload)
- Backend validate authorization (owner, DRAFT status)

---

## 9. Test cURL

### 9.1. Health Check

```bash
curl http://localhost:9999/files/health
```

### 9.2. Upload File

```bash
# 1. Login
TOKEN=$(curl -s -X POST http://localhost:9999/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"lecturer","password":"lecturer123"}' \
  | jq -r '.data.token')

# 2. Upload
curl -X POST http://localhost:9999/files/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test.pdf" \
  -F "syllabus_version_id=1"
```

### 9.3. Get Signed URL

```bash
curl -X GET "http://localhost:9999/files/1/signed-url?expires_in=3600" \
  -H "Authorization: Bearer $TOKEN"
```

### 9.4. Download File

```bash
# Get signed URL
SIGNED_URL=$(curl -s -X GET "http://localhost:9999/files/1/signed-url?expires_in=3600" \
  -H "Authorization: Bearer $TOKEN" \
  | jq -r '.data.signed_url')

# Download
curl "$SIGNED_URL" -o downloaded_file.pdf
```

---

## 10. Production Checklist

- [ ] `FILE_STORAGE_ENABLED=true` trong `.env`
- [ ] `SUPABASE_URL` set đúng (cloud URL hoặc production Supabase)
- [ ] `SUPABASE_SERVICE_ROLE_KEY` set đúng (production key)
- [ ] `SUPABASE_BUCKET` đã tạo trong Supabase
- [ ] Bucket là **private** (không public)
- [ ] Test upload/download thành công
- [ ] Health check trả `enabled: true, configured: true`
- [ ] File size limit phù hợp với production (`MAX_UPLOAD_MB`)
- [ ] Signed URL expiration phù hợp (`SUPABASE_SIGNED_URL_EXPIRES_IN`)

---

**File Storage đã được tích hợp đầy đủ và sẵn sàng sử dụng.**
