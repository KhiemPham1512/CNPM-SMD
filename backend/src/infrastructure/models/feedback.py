from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from infrastructure.databases.base import Base


class Feedback(Base):
    __tablename__ = 'feedback'

    feedback_id = Column(Integer, primary_key=True, autoincrement=True)
    syllabus_id = Column(Integer, ForeignKey('syllabus.syllabus_id'), nullable=False)
    version_id = Column(Integer, ForeignKey('syllabus_version.version_id'), nullable=False)
    author_user_id = Column(Integer, ForeignKey('user.user_id'), nullable=False)
    rating = Column(Integer, nullable=False)
    content = Column(String(2000), nullable=False)
    created_at = Column(DateTime, nullable=False)

    # Relationships
    syllabus = relationship('Syllabus', back_populates='feedbacks')
    version = relationship('SyllabusVersion', back_populates='feedbacks')
    author = relationship('User', foreign_keys=[author_user_id], back_populates='feedbacks')

    def __repr__(self):
        return f"<Feedback(feedback_id='{self.feedback_id}', syllabus_id='{self.syllabus_id}', version_id='{self.version_id}')>"

