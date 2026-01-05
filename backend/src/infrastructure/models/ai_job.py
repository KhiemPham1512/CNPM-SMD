from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from infrastructure.databases.base import Base


class AiJob(Base):
    __tablename__ = 'ai_job'

    job_id = Column(Integer, primary_key=True, autoincrement=True)
    version_id = Column(Integer, ForeignKey('syllabus_version.version_id'), nullable=False)
    job_type = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False)
    requested_by = Column(Integer, ForeignKey('user.user_id'), nullable=False)
    requested_at = Column(DateTime, nullable=False)
    finished_at = Column(DateTime, nullable=True)

    # Relationships
    version = relationship('SyllabusVersion', back_populates='ai_jobs')
    requester = relationship('User', foreign_keys=[requested_by], back_populates='ai_jobs')
    ai_summaries = relationship('AiSummary', back_populates='job')

    def __repr__(self):
        return f"<AiJob(job_id='{self.job_id}', version_id='{self.version_id}', job_type='{self.job_type}')>"

