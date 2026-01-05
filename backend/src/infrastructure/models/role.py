from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import relationship
from infrastructure.databases.base import Base


class Role(Base):
    __tablename__ = 'role'

    role_id = Column(Integer, primary_key=True, autoincrement=True)
    role_name = Column(String(255), nullable=False)

    # Relationships
    user_roles = relationship('UserRole', back_populates='role')
    role_permissions = relationship('RolePermission', back_populates='role')

    def __repr__(self):
        return f"<Role(role_id='{self.role_id}', role_name='{self.role_name}')>"

