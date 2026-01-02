from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from config.postgresql import Base

class OilQuality(Base):
    __tablename__ = "oil_quality"
    oil_id = Column(Integer, primary_key=True, index=True)
    oil_grade = Column(String)
    description = Column(String)
    vehicles = relationship("Vehicle", back_populates="oil_quality")