from sqlalchemy import Column, Integer, String, DECIMAL, ForeignKey, TIMESTAMP, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.postgresql import Base


class Vehicle(Base):
    __tablename__ = "vehicles"

    vehicle_id = Column(Integer, primary_key=True, index=True)

    # Foreign Keys
    model_id = Column(Integer, ForeignKey("models.model_id"))
    class_id = Column(Integer, ForeignKey("vehicle_classes.class_id"))
    engine_type_id = Column(Integer, ForeignKey("engine_types.engine_type_id"))
    fuel_type_id = Column(Integer, ForeignKey("fuel_types.fuel_type_id"))
    transmission_id = Column(Integer, ForeignKey("transmissions.transmission_id"))
    oil_id = Column(Integer, ForeignKey("oil_quality.oil_id"))

    # Attributes
    tyre_size = Column(String)
    manufacturing_year = Column(Integer)
    fuel_efficiency_highway = Column(DECIMAL(5, 2))
    fuel_efficiency_combined = Column(DECIMAL(5, 2))
    description = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Relationships
    model = relationship("Model", back_populates="vehicles")
    vehicle_class = relationship("VehicleClass", back_populates="vehicles")
    engine_type = relationship("EngineType", back_populates="vehicles")
    fuel_type = relationship("FuelType", back_populates="vehicles")
    transmission = relationship("Transmission", back_populates="vehicles")
    oil_quality = relationship("OilQuality", back_populates="vehicles")

    maintenance_costs = relationship("MaintenanceCost", back_populates="vehicle")
