from sqlalchemy import Column, Integer, String, DECIMAL, ForeignKey, Date
from sqlalchemy.orm import relationship
from config.postgresql import Base


class MaintenanceCost(Base):
    __tablename__ = "maintenance_costs"

    record_id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.vehicle_id", ondelete="CASCADE"))

    yearly_cost = Column(DECIMAL(10, 2))
    recorded_date = Column(Date)
    source = Column(String)

    vehicle = relationship("Vehicle", back_populates="maintenance_costs")