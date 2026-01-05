from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from infrastructure.databases.base import Base


class Clo(Base):
    __tablename__ = 'clo'

    clo_id = Column(Integer, primary_key=True, autoincrement=True)
    version_id = Column(Integer, ForeignKey('syllabus_version.version_id'), nullable=False)
    clo_code = Column(String(50), nullable=False)
    description = Column(String(1000), nullable=False)

    # Relationships
    version = relationship('SyllabusVersion', back_populates='clos')
    clo_plo_maps = relationship('CloPloMap', back_populates='clo')

    def __repr__(self):
        return f"<Clo(clo_id='{self.clo_id}', version_id='{self.version_id}', clo_code='{self.clo_code}')>"

