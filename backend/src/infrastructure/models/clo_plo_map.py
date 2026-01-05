from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from infrastructure.databases.base import Base


class CloPloMap(Base):
    __tablename__ = 'clo_plo_map'

    map_id = Column(Integer, primary_key=True, autoincrement=True)
    clo_id = Column(Integer, ForeignKey('clo.clo_id'), nullable=False)
    plo_id = Column(Integer, ForeignKey('plo.plo_id'), nullable=False)
    mapping_level = Column(String(50), nullable=False)

    # Relationships
    clo = relationship('Clo', back_populates='clo_plo_maps')
    plo = relationship('Plo', back_populates='clo_plo_maps')

    def __repr__(self):
        return f"<CloPloMap(map_id='{self.map_id}', clo_id='{self.clo_id}', plo_id='{self.plo_id}')>"

