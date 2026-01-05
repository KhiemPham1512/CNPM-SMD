from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from infrastructure.databases.base import Base


class ReviewRound(Base):
    __tablename__ = 'review_round'

    round_id = Column(Integer, primary_key=True, autoincrement=True)
    version_id = Column(Integer, ForeignKey('syllabus_version.version_id'), nullable=False)
    level = Column(String(50), nullable=False)
    start_at = Column(DateTime, nullable=False)
    end_at = Column(DateTime, nullable=False)
    created_by = Column(Integer, ForeignKey('user.user_id'), nullable=False)

    # Relationships
    version = relationship('SyllabusVersion', back_populates='review_rounds')
    creator = relationship('User', foreign_keys=[created_by], back_populates='review_rounds_created')
    review_comments = relationship('ReviewComment', back_populates='round')

    def __repr__(self):
        return f"<ReviewRound(round_id='{self.round_id}', version_id='{self.version_id}', level='{self.level}')>"

