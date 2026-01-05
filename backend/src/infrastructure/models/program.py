from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from infrastructure.databases.base import Base


class Program(Base):
    __tablename__ = 'program'

    program_id = Column(Integer, primary_key=True, autoincrement=True)
    department_id = Column(Integer, ForeignKey('department.department_id'), nullable=False)
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)

    # Relationships
    department = relationship('Department', back_populates='programs')
    plos = relationship('Plo', back_populates='program')
    syllabi = relationship('Syllabus', back_populates='program')

    def __repr__(self):
        return f"<Program(program_id='{self.program_id}', code='{self.code}')>"

