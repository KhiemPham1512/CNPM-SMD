from sqlalchemy import Column, String, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from infrastructure.databases.base import Base


class AssessmentItem(Base):
    __tablename__ = 'assessment_item'

    assess_id = Column(Integer, primary_key=True, autoincrement=True)
    version_id = Column(Integer, ForeignKey('syllabus_version.version_id'), nullable=False)
    name = Column(String(255), nullable=False)
    weight_percent = Column(Float, nullable=False)
    description = Column(String(1000), nullable=True)

    # Relationships
    version = relationship('SyllabusVersion', back_populates='assessment_items')

    def __repr__(self):
        return f"<AssessmentItem(assess_id='{self.assess_id}', version_id='{self.version_id}', name='{self.name}')>"

