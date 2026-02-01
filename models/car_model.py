from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from config.postgresql import Base

class Model(Base):
    __tablename__ = "models"

    model_id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, ForeignKey("brands.brand_id", ondelete="CASCADE"), nullable=False)
    model_name = Column(String, nullable=False)
    start_year = Column(Integer)
    end_year = Column(Integer)

    brand = relationship("Brand", back_populates="models")
    vehicles = relationship("Vehicle", back_populates="model")

