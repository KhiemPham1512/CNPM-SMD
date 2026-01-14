# Kiến trúc Hệ thống

---

## 1. Clean Architecture Overview

Hệ thống SMD được thiết kế theo **Clean Architecture** principles, đảm bảo separation of concerns và maintainability.

### 1.1. Nguyên tắc Clean Architecture

- **Dependency Rule:** Dependencies chỉ hướng vào trong (inner layers không phụ thuộc outer layers)
- **Independence:** Business logic độc lập với framework, database, UI
- **Testability:** Dễ dàng test business logic mà không cần database hoặc framework
- **Flexibility:** Dễ dàng thay đổi framework, database mà không ảnh hưởng business logic

### 1.2. Layers

```
┌─────────────────────────────────────┐
│         API Layer (Controllers)     │  ← HTTP requests/responses
├─────────────────────────────────────┤
│      Services Layer (Business)      │  ← Business logic, transactions
├─────────────────────────────────────┤
│      Domain Layer (Core)            │  ← Business models, interfaces
├─────────────────────────────────────┤
│   Infrastructure Layer (External)   │  ← Database, Storage, External APIs
└─────────────────────────────────────┘
```

---

## 2. Layer Structure

### 2.1. API Layer (`backend/src/api/`)

**Responsibility:** Xử lý HTTP requests và responses.

**Components:**
- **Controllers:** Parse requests, call services, return responses
- **Schemas:** Marshmallow schemas cho validation và serialization
- **Routes:** Blueprint registration
- **Middleware:** Error handling, CORS, logging
- **Utils:** Authorization utilities (`authz.py`), DB session management (`db.py`)

**Example:**
```python
# api/controllers/syllabus_controller.py
@bp.route('/', methods=['POST'])
@token_required
@role_required(ROLE_LECTURER)
def create_draft() -> Tuple[Response, int]:
    # Parse request
    data = create_schema.load(request.json)
    user_id = get_user_id_from_token()
    
    # Call service
    syllabus_service = container.syllabus_service(db)
    syllabus = syllabus_service.create_draft(...)
    
    # Return response
    return success_response(data, message)
```

**Key Points:**
- Controllers KHÔNG chứa business logic
- Controllers KHÔNG truy cập database trực tiếp
- Controllers chỉ parse requests và format responses

---

### 2.2. Domain Layer (`backend/src/domain/`)

**Responsibility:** Core business logic, không phụ thuộc framework.

**Components:**
- **Models:** Pure Python classes (business entities)
- **Interfaces:** Repository interfaces (abstractions)
- **Exceptions:** Custom exceptions
- **Constants:** Business constants (roles, workflow states)
- **Services:** Domain services (password_hasher, auth_service)

**Example:**
```python
# domain/models/syllabus.py
class Syllabus:
    """Domain model - pure Python class"""
    def __init__(self, syllabus_id, subject_id, program_id, ...):
        self.syllabus_id = syllabus_id
        self.subject_id = subject_id
        # ... business logic methods
```

**Key Points:**
- Domain models là pure Python (không phụ thuộc SQLAlchemy)
- Repository interfaces định nghĩa contracts (không implementation)
- Business logic ở đây, không ở Infrastructure

---

### 2.3. Infrastructure Layer (`backend/src/infrastructure/`)

**Responsibility:** Tương tác với external systems (database, storage, APIs).

**Components:**
- **Databases:** Database adapters (MSSQL, PostgreSQL)
- **Models:** SQLAlchemy models (database schema)
- **Repositories:** Repository implementations (data access)
- **Services:** External services (Supabase Storage, email, etc.)

**Example:**
```python
# infrastructure/models/syllabus.py
class Syllabus(Base):  # SQLAlchemy model
    __tablename__ = 'syllabus'
    syllabus_id = Column(Integer, primary_key=True)
    # ... database columns

# infrastructure/repositories/syllabus_repository.py
class SyllabusRepository(ISyllabusRepository):
    def create(self, syllabus: Syllabus) -> Syllabus:
        # Convert domain model to SQLAlchemy model
        db_model = self._to_db_model(syllabus)
        self.session.add(db_model)
        self.session.commit()
        # Convert back to domain model
        return self._to_domain(db_model)
```

**Key Points:**
- Infrastructure models là SQLAlchemy models (database schema)
- Repositories convert giữa domain models và infrastructure models
- Infrastructure phụ thuộc Domain (qua interfaces), không ngược lại

---

### 2.4. Services Layer (`backend/src/services/`)

**Responsibility:** Application services, orchestrate business logic.

**Components:**
- **Services:** `user_service.py`, `syllabus_service.py`, `file_service.py`
- **Authz:** Authorization policies (`file_access_policy.py`, `file_mutation_policy.py`)

**Example:**
```python
# services/syllabus_service.py
class SyllabusService:
    def __init__(self, repository: ISyllabusRepository, session: Session):
        self.repository = repository
        self.session = session
    
    def create_draft(self, subject_id, program_id, user_id):
        # Business logic
        # Validate FK existence
        # Create domain model
        # Call repository
        # Transaction management
        # Return domain model
```

**Key Points:**
- Services chứa business logic và transaction boundaries
- Services coordinate giữa repositories và external services
- Services không phụ thuộc framework (Flask)

---

## 3. Dependency Flow

### 3.1. Dependency Direction

```
API Layer
  ↓ depends on
Services Layer
  ↓ depends on
Domain Layer (interfaces)
  ↑ implemented by
Infrastructure Layer
```

**Rule:** Dependencies chỉ hướng vào trong. Outer layers phụ thuộc inner layers, không ngược lại.

### 3.2. Dependency Injection

**Container:** `dependency_container.py`

```python
class DependencyContainer:
    def syllabus_service(self, session: Session) -> SyllabusService:
        repository = SyllabusRepository(session)
        return SyllabusService(repository, session)
```

**Usage:**
```python
# In controller
syllabus_service = container.syllabus_service(db)
```

**Benefits:**
- Loose coupling
- Easy to test (mock dependencies)
- Easy to swap implementations

---

## 4. Tech Stack

### 4.1. Backend

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Framework** | Flask | 2.0+ | Web framework |
| **ORM** | SQLAlchemy | 1.4+ | Database ORM |
| **Validation** | Marshmallow | 3.x | Schema validation |
| **Auth** | PyJWT | 2.8+ | JWT tokens |
| **Storage** | Supabase | 2.0+ | File storage |
| **API Docs** | APISpec + Swagger UI | - | OpenAPI 3.0 |

### 4.2. Frontend

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Framework** | React | 18 | UI framework |
| **Build Tool** | Vite | Latest | Build tool |
| **Language** | TypeScript | Latest | Type safety |
| **Styling** | TailwindCSS | Latest | CSS framework |
| **Routing** | React Router | v6 | Client-side routing |
| **Forms** | react-hook-form + zod | Latest | Form management |

### 4.3. Database

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Primary DB** | MSSQL Server | Business data |
| **Storage** | Supabase Storage | File storage |

---

## 5. Design Patterns

### 5.1. Repository Pattern

**Purpose:** Abstraction cho data access layer.

**Interface (Domain):**
```python
# domain/models/isyllabus_repository.py
class ISyllabusRepository(ABC):
    @abstractmethod
    def create(self, syllabus: Syllabus) -> Syllabus:
        pass
    
    @abstractmethod
    def find_by_id(self, syllabus_id: int) -> Optional[Syllabus]:
        pass
```

**Implementation (Infrastructure):**
```python
# infrastructure/repositories/syllabus_repository.py
class SyllabusRepository(ISyllabusRepository):
    def create(self, syllabus: Syllabus) -> Syllabus:
        # Convert domain → infrastructure
        db_model = self._to_db_model(syllabus)
        self.session.add(db_model)
        self.session.commit()
        # Convert infrastructure → domain
        return self._to_domain(db_model)
```

**Benefits:**
- Business logic không phụ thuộc database
- Dễ test (mock repository)
- Dễ swap database

---

### 5.2. Dependency Injection

**Container Pattern:**
```python
# dependency_container.py
class DependencyContainer:
    def __init__(self):
        self._repositories = {}
        self._services = {}
    
    def syllabus_service(self, session: Session) -> SyllabusService:
        if 'syllabus_service' not in self._services:
            repository = self.syllabus_repository(session)
            self._services['syllabus_service'] = SyllabusService(repository, session)
        return self._services['syllabus_service']
```

**Usage:**
```python
# In controller
container = DependencyContainer()
syllabus_service = container.syllabus_service(db)
```

---

### 5.3. Factory Pattern

**Example:**
```python
# infrastructure/services/supabase_storage.py
def get_supabase_storage_service() -> SupabaseStorageService:
    """Factory function to get service from Flask config"""
    file_storage_enabled = current_app.config.get('FILE_STORAGE_ENABLED', False)
    if not file_storage_enabled:
        raise ValueError("File storage is disabled")
    
    supabase_url = current_app.config.get('SUPABASE_URL')
    service_role_key = current_app.config.get('SUPABASE_SERVICE_ROLE_KEY')
    bucket = current_app.config.get('SUPABASE_BUCKET', 'syllabus-files')
    
    return SupabaseStorageService(supabase_url, service_role_key, bucket)
```

---

## 6. File Structure

### 6.1. Backend Structure

```
backend/src/
├── api/                    # API Layer
│   ├── controllers/        # 8 controllers
│   ├── schemas/            # Marshmallow schemas
│   ├── utils/              # authz.py, db.py
│   ├── middleware.py
│   ├── responses.py
│   ├── routes.py
│   └── swagger.py
│
├── domain/                 # Domain Layer
│   ├── constants.py
│   ├── exceptions.py
│   ├── models/            # Domain models + interfaces
│   └── services/          # Domain services
│
├── infrastructure/         # Infrastructure Layer
│   ├── databases/         # Database adapters
│   ├── models/            # SQLAlchemy models (25+)
│   ├── repositories/      # Repository implementations
│   └── services/          # External services (Supabase)
│
├── services/              # Services Layer
│   ├── user_service.py
│   ├── syllabus_service.py
│   ├── file_service.py
│   └── authz/            # Authorization policies
│
├── app.py                 # Flask app factory
├── config.py              # Configuration
└── dependency_container.py
```

### 6.2. Frontend Structure

```
frontend/src/
├── app/                   # App config
│   ├── router.tsx
│   └── store/            # Context providers
│
├── components/            # Reusable components
│   ├── ui/               # Button, Input, Table, etc.
│   ├── workflow/         # StatusBadge, WorkflowTimeline
│   └── syllabi/          # VersionAttachments
│
├── features/             # Feature pages
│   ├── auth/
│   ├── dashboard/
│   ├── syllabi/
│   ├── users/
│   ├── hod/
│   ├── aa/
│   ├── principal/
│   ├── admin/
│   └── student/
│
├── services/             # API services
├── types/                # TypeScript types
└── utils/                # Utilities
```

---

## 7. Data Flow Example

### 7.1. Create Syllabus Flow

```
1. Frontend → POST /syllabi
   ↓
2. Controller (API Layer)
   - Parse request
   - Validate schema
   - Extract user_id from JWT
   ↓
3. Service (Services Layer)
   - Validate business rules
   - Create domain model
   - Call repository
   ↓
4. Repository (Infrastructure Layer)
   - Convert domain → infrastructure model
   - Save to database
   - Convert infrastructure → domain model
   ↓
5. Service
   - Return domain model
   ↓
6. Controller
   - Serialize domain model
   - Return JSON response
   ↓
7. Frontend
   - Display success message
```

---

## 8. Benefits của Clean Architecture

1. **Maintainability:** Dễ maintain, code organized rõ ràng
2. **Testability:** Dễ test business logic (mock repositories)
3. **Flexibility:** Dễ thay đổi framework, database
4. **Scalability:** Dễ scale từng layer độc lập
5. **Team Collaboration:** Dễ phân công work (mỗi layer một team)

---

## 9. References

- **Clean Architecture:** Robert C. Martin
- **Repository Pattern:** Domain-Driven Design
- **Dependency Injection:** Design Patterns

---

**Kiến trúc này đảm bảo hệ thống dễ maintain, test, và scale.**
