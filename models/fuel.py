from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from config.postgresql import Base

class FuelType(Base):
    __tablename__ = "fuel_types"
    fuel_type_id = Column(Integer, primary_key=True, index=True)
    fuel_type_name = Column(String, nullable=False)
    vehicles = relationship("Vehicle", back_populates="fuel_type")