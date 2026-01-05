from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from infrastructure.databases.base import Base


class ReviewComment(Base):
    __tablename__ = 'review_comment'

    comment_id = Column(Integer, primary_key=True, autoincrement=True)
    round_id = Column(Integer, ForeignKey('review_round.round_id'), nullable=False)
    version_id = Column(Integer, ForeignKey('syllabus_version.version_id'), nullable=False)
    author_user_id = Column(Integer, ForeignKey('user.user_id'), nullable=False)
    target_section_id = Column(Integer, ForeignKey('syllabus_section.section_id'), nullable=True)
    comment_text = Column(String(2000), nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    is_resolved = Column(Boolean, nullable=False)

    # Relationships
    round = relationship('ReviewRound', back_populates='review_comments')
    version = relationship('SyllabusVersion', foreign_keys=[version_id], back_populates='review_comments')
    author = relationship('User', foreign_keys=[author_user_id], back_populates='review_comments')
    target_section = relationship('SyllabusSection', foreign_keys=[target_section_id], back_populates='review_comments')

    def __repr__(self):
        return f"<ReviewComment(comment_id='{self.comment_id}', round_id='{self.round_id}', version_id='{self.version_id}')>"

