from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import relationship
from infrastructure.databases.base import Base


class Department(Base):
    __tablename__ = 'department'

    department_id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)

    # Relationships
    programs = relationship('Program', back_populates='department')
    subjects = relationship('Subject', back_populates='department')

    def __repr__(self):
        return f"<Department(department_id='{self.department_id}', code='{self.code}')>"

