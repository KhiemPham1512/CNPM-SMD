# Running SMD Backend on Windows with MSSQL

## Prerequisites

1. **Python 3.8+** installed
2. **MSSQL Server** running (Docker or local installation)
3. **Virtual environment** activated

## Step 1: Setup Environment

### 1.1 Create Virtual Environment (if not exists)

```powershell
# From backend/src directory
python -m venv ..\..\.venv
```

### 1.2 Activate Virtual Environment

```powershell
# From backend/src directory
..\..\.venv\Scripts\Activate.ps1
```

If you get execution policy error:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 1.3 Install Dependencies

```powershell
# From backend/src directory
pip install -r requirements.txt
```

## Step 2: Database Setup

### 2.1 Start MSSQL Server (Docker)

```powershell
docker run -e "ACCEPT_EULA=Y" -e "MSSQL_SA_PASSWORD=Aa@123456" -p 1433:1433 --name sql1 --hostname sql1 -d mcr.microsoft.com/mssql/server:2025-latest
```

Wait 30-60 seconds for SQL Server to be ready. Check logs:
```powershell
docker logs sql1
```

### 2.2 Create .env File

Copy `.env.example` to `.env` in `backend/src/` directory:

```powershell
# From backend/src directory
Copy-Item .env.example .env
```

Edit `.env` and set:
- `DATABASE_URI` with your MSSQL connection string
- `SECRET_KEY` (use a strong random string)

Example `.env`:
```
FLASK_ENV=development
DEBUG=True
SECRET_KEY=your-secret-key-here
DATABASE_URI=mssql+pymssql://sa:Aa%40123456@127.0.0.1:1433/smd
```

**Note:** URL encode special characters in password (e.g., `@` becomes `%40`)

### 2.3 Test Database Connection

```powershell
python -m scripts.test_connection
```

### 2.4 Seed Database (Optional but Recommended)

This creates 6 roles and demo users:

```powershell
python -m scripts.seed_mvp
```

**Demo Users Created:**
- `admin` / `admin123` (ADMIN)
- `lecturer` / `lecturer123` (LECTURER)
- `hod` / `hod123` (HOD)
- `aa` / `aa123` (AA)
- `principal` / `principal123` (PRINCIPAL)
- `student` / `student123` (STUDENT)

## Step 3: Run Backend

### 3.1 Start Flask Application

```powershell
# From backend/src directory
python app.py
```

Or using Flask CLI:
```powershell
flask run --host=0.0.0.0 --port=9999
```

### 3.2 Verify Backend is Running

- Backend should start on `http://127.0.0.1:9999`
- Swagger UI: `http://127.0.0.1:9999/docs`
- API Spec: `http://127.0.0.1:9999/swagger.json`

## Step 4: Test API

### 4.1 Login to Get Token

**Option A: Using Swagger UI (Recommended)**
1. Open `http://127.0.0.1:9999/docs` in browser
2. Find `POST /auth/login` endpoint
3. Click "Try it out"
4. Enter credentials:
   - username: `admin`
   - password: `admin123`
5. Click "Execute"
6. Copy the `token` value from the response (the full token string, not truncated)
7. Click the "Authorize" button (top right, lock icon)
8. Paste ONLY the token (without "Bearer " prefix) in the "Value" field
9. Click "Authorize" then "Close"
10. Now all protected endpoints will use this token automatically

**Option B: Using PowerShell**

```powershell
# Using PowerShell (Invoke-RestMethod)
$body = @{
    username = "admin"
    password = "admin123"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://127.0.0.1:9999/auth/login" -Method POST -Body $body -ContentType "application/json"
$token = $response.data.token
Write-Host "Token: $token"
Write-Host "Full token length: $($token.Length) characters"
```

**Important:** When copying token, ensure you copy the COMPLETE token (should be ~150+ characters). If token appears truncated with `...`, expand the response to see full token.

### 4.2 Test Protected Endpoint

**Using Swagger UI:**
- After authorizing (step 4.1), just click "Execute" on any protected endpoint

**Using PowerShell:**
```powershell
$headers = @{
    Authorization = "Bearer $token"
}

Invoke-RestMethod -Uri "http://127.0.0.1:9999/users" -Method GET -Headers $headers
```

### 4.3 Test /auth/me Endpoint

**Using Swagger UI:**
1. Ensure you're authorized (see 4.1)
2. Find `GET /auth/me` endpoint
3. Click "Execute"
4. Should return 200 with user info and roles

**Using PowerShell:**
```powershell
$headers = @{
    Authorization = "Bearer $token"
}

Invoke-RestMethod -Uri "http://127.0.0.1:9999/auth/me" -Method GET -Headers $headers
```

## Troubleshooting

### Database Connection Failed

1. **Check SQL Server is running:**
   ```powershell
   docker ps | Select-String sql
   ```

2. **Check port 1433 is accessible:**
   ```powershell
   Test-NetConnection -ComputerName 127.0.0.1 -Port 1433
   ```

3. **Verify DATABASE_URI in .env:**
   - Check password is URL-encoded
   - Check database name exists
   - Check username/password are correct

### Port Already in Use

If port 9999 is in use, change it in `app.py`:
```python
app.run(host='0.0.0.0', port=9999, debug=True)  # Change 9999 to another port
```

### Module Not Found Errors

Ensure you're running from `backend/src` directory and virtual environment is activated.

### JWT Token Issues

**Error: "Malformed JWT (expected 3 segments)"**

This error means the JWT token is incomplete or incorrectly formatted. Common causes:

1. **Token was truncated when copying:**
   - JWT tokens are typically 150+ characters long
   - Ensure you copy the COMPLETE token from login response
   - In Swagger UI, expand the response to see full token (not the truncated `...` version)

2. **Incorrect token format:**
   - Valid JWT has 3 parts separated by dots: `header.payload.signature`
   - Example: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJleHAiOjE3MDQ4...`
   - If you see only 1-2 segments, the token is incomplete

3. **Using token in Swagger UI:**
   - Click "Authorize" button (lock icon, top right)
   - Paste ONLY the token (without "Bearer " prefix)
   - Swagger UI automatically adds "Bearer " prefix
   - Click "Authorize" then "Close"

4. **Verify token is complete:**
   ```powershell
   # After login, check token length
   $token = $response.data.token
   Write-Host "Token length: $($token.Length) characters"
   # Should be 150+ characters for a valid JWT
   ```

**Error: "Token expired"**

- JWT tokens expire after 2 hours
- Simply login again to get a new token

**Error: "Invalid token signature"**

- Usually means SECRET_KEY changed or token was signed with different key
- Ensure SECRET_KEY in `.env` matches the one used when token was created

## Development Tips

- **Auto-reload:** Flask runs in debug mode by default (auto-reloads on code changes)
- **Logs:** Check console output for errors and debug information
- **Swagger UI:** Use `/docs` endpoint to test API interactively
- **Database Changes:** Use migrations or `AUTO_CREATE_TABLES=True` in development

## Production Deployment

For production:
1. Set `DEBUG=False` in `.env`
2. Set strong `SECRET_KEY`
3. Use proper database credentials
4. Set `CORS_ORIGINS` to your frontend domain
5. Use production WSGI server (gunicorn, uwsgi, etc.)
