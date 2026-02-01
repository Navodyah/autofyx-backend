from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from config.postgresql import Base

class Brand(Base):
    __tablename__ = "brands"

    brand_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    brand_name = Column(String, nullable=False)
    country = Column(String)

    models = relationship("Model", back_populates="brand")
