import logging
from domain.models.iuser_repository import IUserRepository
from domain.models.user import User
from typing import List, Optional
from sqlalchemy.orm import Session
from infrastructure.models.user import User as UserModel
from infrastructure.models.user_role import UserRole
from infrastructure.models.role import Role

logger = logging.getLogger(__name__)


class UserRepository(IUserRepository):
    def __init__(self, session: Session):
        self.session = session

    def add(self, user: User) -> User:
        """Add user to session. Does NOT commit - transaction managed by service layer."""
        try:
            user_model = UserModel(
                username=user.username,
                password_hash=user.password_hash,
                full_name=user.full_name,
                email=user.email,
                status=user.status,
                created_at=user.created_at
            )
            self.session.add(user_model)
            self.session.flush()  # Flush to get ID, but don't commit
            self.session.refresh(user_model)
            return self._to_domain(user_model)
        except Exception as e:
            logger.exception(f"Failed to add user to session: {e}")
            raise  # Re-raise original exception to preserve stack trace

    def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID. Read-only operation."""
        try:
            user_model = self.session.query(UserModel).filter_by(user_id=user_id).first()
            if user_model:
                return self._to_domain(user_model)
            return None
        except Exception as e:
            logger.exception(f"Failed to get user by id {user_id}: {e}")
            raise  # Re-raise original exception

    def list(self) -> List[User]:
        """List all users. Read-only operation."""
        try:
            user_models = self.session.query(UserModel).all()
            return [self._to_domain(user_model) for user_model in user_models]
        except Exception as e:
            logger.exception(f"Failed to list users: {e}")
            raise  # Re-raise original exception

    def update(self, user: User) -> User:
        """Update user in session. Does NOT commit - transaction managed by service layer."""
        try:
            user_model = self.session.query(UserModel).filter_by(user_id=user.user_id).first()
            if not user_model:
                raise ValueError('User not found')
            
            user_model.username = user.username
            # Only update password_hash if provided (not None and not empty string)
            if user.password_hash is not None and isinstance(user.password_hash, str) and user.password_hash.strip():
                user_model.password_hash = user.password_hash
            user_model.full_name = user.full_name
            user_model.email = user.email
            user_model.status = user.status
            
            self.session.flush()  # Flush changes, but don't commit
            self.session.refresh(user_model)
            return self._to_domain(user_model)
        except ValueError:
            raise  # Re-raise ValueError as-is
        except Exception as e:
            logger.exception(f"Failed to update user {user.user_id}: {e}")
            raise  # Re-raise original exception

    def delete(self, user_id: int) -> None:
        """Delete user from session. Does NOT commit - transaction managed by service layer."""
        try:
            user_model = self.session.query(UserModel).filter_by(user_id=user_id).first()
            if user_model:
                self.session.delete(user_model)
                self.session.flush()  # Flush deletion, but don't commit
            else:
                raise ValueError('User not found')
        except ValueError:
            raise  # Re-raise ValueError as-is
        except Exception as e:
            logger.exception(f"Failed to delete user {user_id}: {e}")
            raise  # Re-raise original exception

    def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username. Read-only operation."""
        try:
            user_model = self.session.query(UserModel).filter_by(username=username).first()
            if user_model:
                return self._to_domain(user_model)
            return None
        except Exception as e:
            logger.exception(f"Failed to get user by username {username}: {e}")
            raise  # Re-raise original exception

    def get_user_roles(self, user_id: int) -> List[str]:
        """Get list of role names for a user. Read-only operation."""
        try:
            user_roles = self.session.query(UserRole).filter_by(user_id=user_id).all()
            role_ids = [ur.role_id for ur in user_roles]
            if not role_ids:
                return []
            
            roles = self.session.query(Role).filter(Role.role_id.in_(role_ids)).all()
            return [role.role_name for role in roles]
        except Exception as e:
            logger.exception(f"Failed to get user roles for user_id {user_id}: {e}")
            raise  # Re-raise original exception

    def _to_domain(self, user_model: UserModel) -> User:
        """Convert database model to domain model."""
        return User(
            user_id=user_model.user_id,
            username=user_model.username,
            password_hash=user_model.password_hash,  # Internal use only - never exposed in API
            full_name=user_model.full_name,
            email=user_model.email,
            status=user_model.status,
            created_at=user_model.created_at
        )
