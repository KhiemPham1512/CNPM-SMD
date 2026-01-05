from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from infrastructure.databases.base import Base


class AiSummary(Base):
    __tablename__ = 'ai_summary'

    summary_id = Column(Integer, primary_key=True, autoincrement=True)
    version_id = Column(Integer, ForeignKey('syllabus_version.version_id'), nullable=False)
    job_id = Column(Integer, ForeignKey('ai_job.job_id'), nullable=False)
    summary_text = Column(String(5000), nullable=False)
    generated_at = Column(DateTime, nullable=False)

    # Relationships
    version = relationship('SyllabusVersion', back_populates='ai_summaries')
    job = relationship('AiJob', back_populates='ai_summaries')

    def __repr__(self):
        return f"<AiSummary(summary_id='{self.summary_id}', version_id='{self.version_id}', job_id='{self.job_id}')>"

