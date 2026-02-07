from sqlalchemy import Column, Integer, String, DECIMAL
from sqlalchemy.orm import relationship
from config.postgresql import Base


class EngineType(Base):
    __tablename__ = "engine_types"
    engine_type_id = Column(Integer, primary_key=True, index=True)
    engine_type_name = Column(String)
    cylinders = Column(Integer)
    vehicles = relationship("Vehicle", back_populates="engine_type")