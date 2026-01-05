from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from infrastructure.databases.base import Base


class Subscription(Base):
    __tablename__ = 'subscription'

    sub_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('user.user_id'), nullable=False)
    syllabus_id = Column(Integer, ForeignKey('syllabus.syllabus_id'), nullable=False)
    created_at = Column(DateTime, nullable=False)

    # Relationships
    user = relationship('User', back_populates='subscriptions')
    syllabus = relationship('Syllabus', back_populates='subscriptions')

    def __repr__(self):
        return f"<Subscription(sub_id='{self.sub_id}', user_id='{self.user_id}', syllabus_id='{self.syllabus_id}')>"

