from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from infrastructure.databases.base import Base


class Syllabus(Base):
    __tablename__ = 'syllabus'

    syllabus_id = Column(Integer, primary_key=True, autoincrement=True)
    subject_id = Column(Integer, ForeignKey('subject.subject_id'), nullable=False)
    program_id = Column(Integer, ForeignKey('program.program_id'), nullable=False)
    owner_lecturer_id = Column(Integer, ForeignKey('user.user_id'), nullable=False)
    current_version_id = Column(Integer, ForeignKey('syllabus_version.version_id'), nullable=True)
    lifecycle_status = Column(String(50), nullable=False)
    created_at = Column(DateTime, nullable=False)

    # Relationships
    subject = relationship('Subject', back_populates='syllabi')
    program = relationship('Program', back_populates='syllabi')
    owner = relationship('User', foreign_keys=[owner_lecturer_id], back_populates='syllabus_owner')
    current_version = relationship('SyllabusVersion', foreign_keys=[current_version_id], post_update=True)
    versions = relationship('SyllabusVersion', back_populates='syllabus')
    subscriptions = relationship('Subscription', back_populates='syllabus')
    feedbacks = relationship('Feedback', back_populates='syllabus')

    def __repr__(self):
        return f"<Syllabus(syllabus_id='{self.syllabus_id}', subject_id='{self.subject_id}')>"

