from sqlalchemy import Column, String, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
from infrastructure.databases.base import Base


class SyllabusSection(Base):
    __tablename__ = 'syllabus_section'

    section_id = Column(Integer, primary_key=True, autoincrement=True)
    version_id = Column(Integer, ForeignKey('syllabus_version.version_id'), nullable=False)
    section_key = Column(String(100), nullable=False)
    title = Column(String(255), nullable=False)
    content_text = Column(Text, nullable=True)

    # Relationships
    version = relationship('SyllabusVersion', back_populates='sections')
    review_comments = relationship('ReviewComment', back_populates='target_section')

    def __repr__(self):
        return f"<SyllabusSection(section_id='{self.section_id}', version_id='{self.version_id}', section_key='{self.section_key}')>"

