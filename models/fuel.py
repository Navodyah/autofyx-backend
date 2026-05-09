from sqlalchemy import Column, Integer, Numeric, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from config.postgresql import Base

class FuelType(Base):
    __tablename__ = "fuel_types"
    fuel_type_id = Column(Integer, primary_key=True, index=True)
    fuel_type_name = Column(String, nullable=False)
    fuel_price = Column(Numeric(12, 2), nullable=True)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    vehicles = relationship("Vehicle", back_populates="fuel_type")