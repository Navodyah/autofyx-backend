from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from config.postgresql import Base


class Transmission(Base):
    __tablename__ = "transmissions"
    transmission_id = Column(Integer, primary_key=True, index=True)
    transmission_name = Column(String, nullable=False)
    category = Column(String)
    vehicles = relationship("Vehicle", back_populates="transmission")