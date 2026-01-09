from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from infrastructure.databases.base import Base


class SystemSetting(Base):
    __tablename__ = 'system_setting'

    setting_id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(50), nullable=False, unique=True, index=True)
    value = Column(String(1000), nullable=False)
    data_type = Column(String(50), nullable=False)
    updated_at = Column(DateTime, nullable=False)
    updated_by = Column(Integer, ForeignKey('user.user_id'), nullable=True)

    # Relationships
    updater = relationship('User', foreign_keys=[updated_by], back_populates='system_settings')

    def __repr__(self):
        return f"<SystemSetting(setting_id='{self.setting_id}', key='{self.key}', data_type='{self.data_type}')>"

