from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from infrastructure.databases.base import Base


class WorkflowAction(Base):
    __tablename__ = 'workflow_action'

    action_id = Column(Integer, primary_key=True, autoincrement=True)
    version_id = Column(Integer, ForeignKey('syllabus_version.version_id'), nullable=False)
    actor_user_id = Column(Integer, ForeignKey('user.user_id'), nullable=False)
    action_type = Column(String(50), nullable=False)
    action_note = Column(String(1000), nullable=True)
    action_at = Column(DateTime, nullable=False)

    # Relationships
    version = relationship('SyllabusVersion', back_populates='workflow_actions')
    actor = relationship('User', foreign_keys=[actor_user_id], back_populates='workflow_actions')

    def __repr__(self):
        return f"<WorkflowAction(action_id='{self.action_id}', version_id='{self.version_id}', action_type='{self.action_type}')>"

