from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import relationship
from infrastructure.databases.base import Base


class Permission(Base):
    __tablename__ = 'permission'

    permission_id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)

    # Relationships
    role_permissions = relationship('RolePermission', back_populates='permission')

    def __repr__(self):
        return f"<Permission(permission_id='{self.permission_id}', code='{self.code}')>"

