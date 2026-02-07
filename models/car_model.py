from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from config.postgresql import Base

class Model(Base):
    __tablename__ = "models"

    model_id = Column(Integer, primary_key=True, index=True)

    model_name = Column(String, nullable=False)
    start_year = Column(Integer)
    end_year = Column(Integer)


