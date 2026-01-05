from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from infrastructure.databases.base import Base


class SubjectRelation(Base):
    __tablename__ = 'subject_relation'

    relation_id = Column(Integer, primary_key=True, autoincrement=True)
    from_subject_id = Column(Integer, ForeignKey('subject.subject_id'), nullable=False)
    to_subject_id = Column(Integer, ForeignKey('subject.subject_id'), nullable=False)
    relation_type = Column(String(50), nullable=False)

    # Relationships
    from_subject = relationship('Subject', foreign_keys=[from_subject_id], back_populates='from_relations')
    to_subject = relationship('Subject', foreign_keys=[to_subject_id], back_populates='to_relations')

    def __repr__(self):
        return f"<SubjectRelation(relation_id='{self.relation_id}', from_subject_id='{self.from_subject_id}', to_subject_id='{self.to_subject_id}')>"

