import logging
from domain.models.user import User
from domain.models.iuser_repository import IUserRepository
from domain.services.password_hasher import IPasswordHasher
from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, repository: IUserRepository, password_hasher: IPasswordHasher, session: Session):
        """
        Initialize UserService with dependencies.
        
        Args:
            repository: User repository
            password_hasher: Password hasher service
            session: Database session (required for all operations, including read-only)
        """
        self.repository = repository
        self.password_hasher = password_hasher
        self.session = session  # Session is always required

    def create_user(self, username: str, password: str, full_name: str, 
                   email: str, status: str = 'active') -> User:
        """
        Create a new user. Password is plain text - will be hashed internally.
        Transaction is managed by this service method.
        """
        try:
            # Hash password before storing
            password_hash = self.password_hasher.hash_password(password)
            
            user = User(
                user_id=None,
                username=username,
                password_hash=password_hash,
                full_name=full_name,
                email=email,
                status=status,
                created_at=datetime.now(timezone.utc)
            )
            user = self.repository.add(user)
            # Commit transaction
            self.session.commit()
            logger.info(f"User created successfully: {username}")
            return user
        except Exception as e:
            self.session.rollback()
            logger.exception(f"Failed to create user {username}: {e}")
            raise

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        return self.repository.get_by_id(user_id)

    def list_users(self) -> List[User]:
        return self.repository.list()

    def update_user_status(self, user_id: int, status: str) -> User:
        """Update user status. Transaction is managed by this service method."""
        try:
            user = self.repository.get_by_id(user_id)
            if not user:
                raise ValueError('User not found')
            
            user.status = status
            user = self.repository.update(user)
            # Commit transaction
            self.session.commit()
            logger.info(f"User status updated: user_id={user_id}, status={status}")
            return user
        except ValueError:
            self.session.rollback()
            raise
        except Exception as e:
            self.session.rollback()
            logger.exception(f"Failed to update user status {user_id}: {e}")
            raise

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user by username and password."""
        user = self.repository.get_by_username(username)
        if not user:
            return None
        
        if not self.password_hasher.verify_password(password, user.password_hash):
            return None
        
        return user

    def get_user_roles(self, user_id: int) -> List[str]:
        """Get list of role names for a user."""
        return self.repository.get_user_roles(user_id)

    def delete_user(self, user_id: int) -> None:
        """Delete a user by ID. Transaction is managed by this service method."""
        try:
            user = self.repository.get_by_id(user_id)
            if not user:
                raise ValueError('User not found')
            
            self.repository.delete(user_id)
            # Commit transaction
            self.session.commit()
            logger.info(f"User deleted: user_id={user_id}")
        except ValueError:
            self.session.rollback()
            raise
        except Exception as e:
            self.session.rollback()
            logger.exception(f"Failed to delete user {user_id}: {e}")
            raise

    def assign_role(self, user_id: int, role_name: str) -> User:
        """
        Assign a role to a user. Transaction is managed by this service method.
        
        Args:
            user_id: User ID
            role_name: Role name (must be one of: ADMIN, LECTURER, HOD, AA, PRINCIPAL, STUDENT)
        
        Returns:
            Updated User object
        
        Raises:
            ValueError: If user not found or role not found
        """
        from infrastructure.models.user import User as UserModel
        from infrastructure.models.role import Role
        from infrastructure.models.user_role import UserRole
        
        try:
            # Validate user exists
            user = self.repository.get_by_id(user_id)
            if not user:
                raise ValueError('User not found')
            
            # Validate role exists
            role = self.session.query(Role).filter_by(role_name=role_name).first()
            if not role:
                raise ValueError(f'Role not found: {role_name}')
            
            # Check if role already assigned
            existing = self.session.query(UserRole).filter_by(
                user_id=user_id,
                role_id=role.role_id
            ).first()
            
            if existing:
                logger.info(f"Role {role_name} already assigned to user {user_id}")
                return user
            
            # Assign role
            user_role = UserRole(user_id=user_id, role_id=role.role_id)
            self.session.add(user_role)
            self.session.commit()
            
            logger.info(f"Role {role_name} assigned to user {user_id}")
            return self.repository.get_by_id(user_id)
        except ValueError:
            self.session.rollback()
            raise
        except Exception as e:
            self.session.rollback()
            logger.exception(f"Failed to assign role {role_name} to user {user_id}: {e}")
            raise

    def assign_roles(self, user_id: int, role_names: List[str]) -> User:
        """
        Assign multiple roles to a user (replaces existing roles).
        Transaction is managed by this service method.
        
        Args:
            user_id: User ID
            role_names: List of role names to assign
        
        Returns:
            Updated User object
        
        Raises:
            ValueError: If user not found or any role not found
        """
        from infrastructure.models.role import Role
        from infrastructure.models.user_role import UserRole
        
        try:
            # Validate user exists
            user = self.repository.get_by_id(user_id)
            if not user:
                raise ValueError('User not found')
            
            # Validate all roles exist BEFORE deleting existing roles (transaction safety)
            validated_roles = []
            for role_name in role_names:
                role = self.session.query(Role).filter_by(role_name=role_name).first()
                if not role:
                    raise ValueError(f'Role not found: {role_name}')
                validated_roles.append(role)
            
            # Only after all roles are validated, proceed with delete + insert
            # Remove all existing roles first
            existing_roles = self.session.query(UserRole).filter_by(user_id=user_id).all()
            for user_role in existing_roles:
                self.session.delete(user_role)
            
            # Assign new roles (all validated)
            for role in validated_roles:
                user_role = UserRole(user_id=user_id, role_id=role.role_id)
                self.session.add(user_role)
            
            self.session.commit()
            logger.info(f"Roles {role_names} assigned to user {user_id}")
            return self.repository.get_by_id(user_id)
        except ValueError:
            self.session.rollback()
            raise
        except Exception as e:
            self.session.rollback()
            logger.exception(f"Failed to assign roles to user {user_id}: {e}")
            raise

    def remove_role(self, user_id: int, role_name: str) -> User:
        """
        Remove a role from a user. Transaction is managed by this service method.
        
        Args:
            user_id: User ID
            role_name: Role name to remove
        
        Returns:
            Updated User object
        
        Raises:
            ValueError: If user not found or role not found
        """
        from infrastructure.models.role import Role
        from infrastructure.models.user_role import UserRole
        
        try:
            # Validate user exists
            user = self.repository.get_by_id(user_id)
            if not user:
                raise ValueError('User not found')
            
            # Validate role exists
            role = self.session.query(Role).filter_by(role_name=role_name).first()
            if not role:
                raise ValueError(f'Role not found: {role_name}')
            
            # Remove role
            user_role = self.session.query(UserRole).filter_by(
                user_id=user_id,
                role_id=role.role_id
            ).first()
            
            if not user_role:
                logger.info(f"Role {role_name} not assigned to user {user_id}")
                return user
            
            self.session.delete(user_role)
            self.session.commit()
            
            logger.info(f"Role {role_name} removed from user {user_id}")
            return self.repository.get_by_id(user_id)
        except ValueError:
            self.session.rollback()
            raise
        except Exception as e:
            self.session.rollback()
            logger.exception(f"Failed to remove role {role_name} from user {user_id}: {e}")
            raise

