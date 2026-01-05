from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from infrastructure.databases.base import Base


class SyllabusVersion(Base):
    __tablename__ = 'syllabus_version'

    version_id = Column(Integer, primary_key=True, autoincrement=True)
    syllabus_id = Column(Integer, ForeignKey('syllabus.syllabus_id'), nullable=False)
    academic_year = Column(String(20), nullable=False)
    version_no = Column(Integer, nullable=False)
    workflow_status = Column(String(50), nullable=False)
    submitted_at = Column(DateTime, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    published_at = Column(DateTime, nullable=True)
    created_by = Column(Integer, ForeignKey('user.user_id'), nullable=False)
    created_at = Column(DateTime, nullable=False)

    # Relationships
    syllabus = relationship('Syllabus', foreign_keys=[syllabus_id], back_populates='versions')
    creator = relationship('User', foreign_keys=[created_by], back_populates='syllabus_versions_created')
    sections = relationship('SyllabusSection', back_populates='version')
    assessment_items = relationship('AssessmentItem', back_populates='version')
    clos = relationship('Clo', back_populates='version')
    review_rounds = relationship('ReviewRound', back_populates='version')
    review_comments = relationship('ReviewComment', back_populates='version')
    workflow_actions = relationship('WorkflowAction', back_populates='version')
    ai_jobs = relationship('AiJob', back_populates='version')
    ai_summaries = relationship('AiSummary', back_populates='version')
    feedbacks = relationship('Feedback', back_populates='version')

    def __repr__(self):
        return f"<SyllabusVersion(version_id='{self.version_id}', syllabus_id='{self.syllabus_id}', version_no={self.version_no})>"

