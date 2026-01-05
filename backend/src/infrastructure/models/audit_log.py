from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from infrastructure.databases.base import Base


class AuditLog(Base):
    __tablename__ = 'audit_log'

    log_id = Column(Integer, primary_key=True, autoincrement=True)
    actor_user_id = Column(Integer, ForeignKey('user.user_id'), nullable=False)
    action = Column(String(100), nullable=False)
    entity_name = Column(String(100), nullable=False)
    entity_id = Column(String(50), nullable=False)
    detail = Column(String(2000), nullable=True)
    created_at = Column(DateTime, nullable=False)

    # Relationships
    actor = relationship('User', foreign_keys=[actor_user_id], back_populates='audit_logs')

    def __repr__(self):
        return f"<AuditLog(log_id='{self.log_id}', actor_user_id='{self.actor_user_id}', action='{self.action}')>"

