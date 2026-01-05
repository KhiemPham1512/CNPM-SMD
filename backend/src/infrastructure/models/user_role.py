from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from infrastructure.databases.base import Base


class UserRole(Base):
    __tablename__ = 'user_role'

    user_id = Column(Integer, ForeignKey('user.user_id'), primary_key=True)
    role_id = Column(Integer, ForeignKey('role.role_id'), primary_key=True)

    # Relationships
    user = relationship('User', back_populates='user_roles')
    role = relationship('Role', back_populates='user_roles')

    def __repr__(self):
        return f"<UserRole(user_id='{self.user_id}', role_id='{self.role_id}')>"

