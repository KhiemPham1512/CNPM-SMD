from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from infrastructure.databases.base import Base


class Plo(Base):
    __tablename__ = 'plo'

    plo_id = Column(Integer, primary_key=True, autoincrement=True)
    program_id = Column(Integer, ForeignKey('program.program_id'), nullable=False)
    plo_code = Column(String(50), nullable=False)
    description = Column(String(1000), nullable=False)
    status = Column(String(50), nullable=False)

    # Relationships
    program = relationship('Program', back_populates='plos')
    clo_plo_maps = relationship('CloPloMap', back_populates='plo')

    def __repr__(self):
        return f"<Plo(plo_id='{self.plo_id}', plo_code='{self.plo_code}')>"

