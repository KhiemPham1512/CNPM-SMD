from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from infrastructure.databases.base import Base


class Subject(Base):
    __tablename__ = 'subject'

    subject_id = Column(Integer, primary_key=True, autoincrement=True)
    department_id = Column(Integer, ForeignKey('department.department_id'), nullable=False)
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    credits = Column(Integer, nullable=False)
    status = Column(String(50), nullable=False)

    # Relationships
    department = relationship('Department', back_populates='subjects')
    syllabi = relationship('Syllabus', back_populates='subject')
    from_relations = relationship('SubjectRelation', foreign_keys='SubjectRelation.from_subject_id', back_populates='from_subject')
    to_relations = relationship('SubjectRelation', foreign_keys='SubjectRelation.to_subject_id', back_populates='to_subject')

    def __repr__(self):
        return f"<Subject(subject_id='{self.subject_id}', code='{self.code}')>"

