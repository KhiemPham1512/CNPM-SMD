"""
Dependency Injection Container

Lightweight DI container for service and repository instantiation.
No external DI framework required.
"""
from infrastructure.repositories.user_repository import UserRepository
from infrastructure.repositories.syllabus_repository import SyllabusRepository
from infrastructure.repositories.file_repository import FileRepository
from infrastructure.services.password_hasher import WerkzeugPasswordHasher
from services.user_service import UserService
from services.syllabus_service import SyllabusService
from services.file_service import FileService
from sqlalchemy.orm import Session


def get_session_local():
    """
    Get SessionLocal factory. Must be called after init_mssql() has been called.
    """
    from infrastructure.databases.mssql import SessionLocal
    if SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_mssql() first.")
    return SessionLocal


class Container:
    """Dependency injection container."""
    
    def __init__(self):
        # Create password hasher instance (stateless, can be singleton)
        self._password_hasher = WerkzeugPasswordHasher()
    
    def user_service(self, db: Session) -> UserService:
        """
        Create UserService with dependencies.
        
        Args:
            db: Database session (required for all operations)
        
        Returns:
            UserService instance with session injected
        """
        if db is None:
            raise ValueError("Database session is required for UserService")
        user_repository = UserRepository(db)
        return UserService(user_repository, self._password_hasher, session=db)
    
    def syllabus_service(self, db: Session) -> SyllabusService:
        """
        Create SyllabusService with dependencies.
        
        Args:
            db: Database session (required for all operations)
        
        Returns:
            SyllabusService instance with session injected
        """
        if db is None:
            raise ValueError("Database session is required for SyllabusService")
        syllabus_repository = SyllabusRepository(db)
        return SyllabusService(syllabus_repository, session=db)
    
    def password_hasher(self):
        """Get password hasher instance."""
        return self._password_hasher
    
    def file_service(self, db: Session) -> FileService:
        """
        Create FileService with dependencies.
        
        Args:
            db: Database session (required for all operations)
        
        Returns:
            FileService instance with session injected
        """
        if db is None:
            raise ValueError("Database session is required for FileService")
        
        # Import here to avoid circular dependencies and ensure Supabase config is loaded
        from infrastructure.services.supabase_storage import get_supabase_storage_service
        
        file_repository = FileRepository(db)
        storage_service = get_supabase_storage_service()
        return FileService(file_repository, storage_service, session=db)


# Global container instance
container = Container()
