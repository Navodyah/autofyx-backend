from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from config.postgresql import Base

class VehicleClass(Base):
    __tablename__ = "vehicle_classes"
    class_id = Column(Integer, primary_key=True, index=True)
    class_name = Column(String, nullable=False)
    vehicles = relationship("Vehicle", back_populates="vehicle_class")