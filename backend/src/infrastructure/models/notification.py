from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from infrastructure.databases.base import Base


class Notification(Base):
    __tablename__ = 'notification'

    noti_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('user.user_id'), nullable=False)
    type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    body = Column(String(2000), nullable=False)
    ref_entity = Column(String(100), nullable=True)
    ref_id = Column(String, nullable=True)
    is_read = Column(Boolean, nullable=False)
    created_at = Column(DateTime, nullable=False)

    # Relationships
    user = relationship('User', back_populates='notifications')

    def __repr__(self):
        return f"<Notification(noti_id='{self.noti_id}', user_id='{self.user_id}', type='{self.type}')>"

