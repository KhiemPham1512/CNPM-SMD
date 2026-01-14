from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.orm import relationship
from infrastructure.databases.base import Base


class User(Base):
    __tablename__ = 'user'

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False)
    created_at = Column(DateTime, nullable=False)

    # Relationships
    user_roles = relationship('UserRole', back_populates='user')
    syllabus_owner = relationship('Syllabus', back_populates='owner')
    syllabus_versions_created = relationship('SyllabusVersion', back_populates='creator')
    review_rounds_created = relationship('ReviewRound', back_populates='creator')
    review_comments = relationship('ReviewComment', back_populates='author')
    workflow_actions = relationship('WorkflowAction', back_populates='actor')
    ai_jobs = relationship('AiJob', back_populates='requester')
    subscriptions = relationship('Subscription', back_populates='user')
    notifications = relationship('Notification', back_populates='user')
    feedbacks = relationship('Feedback', back_populates='author')
    system_settings = relationship('SystemSetting', back_populates='updater')
    audit_logs = relationship('AuditLog', back_populates='actor')
    uploaded_files = relationship('FileAsset', back_populates='uploader')

    def __repr__(self):
        return f"<User(user_id='{self.user_id}', username='{self.username}')>"

