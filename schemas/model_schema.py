from pydantic import BaseModel
from typing import Optional


class ModelBase(BaseModel):
    brand_id: int
    model_name: str
    start_year: Optional[int] = None
    end_year: Optional[int] = None


class ModelCreate(ModelBase):
    pass


class ModelUpdate(BaseModel):
    brand_id: Optional[int] = None
    model_name: Optional[str] = None
    start_year: Optional[int] = None
    end_year: Optional[int] = None


class ModelResponse(ModelBase):
    model_id: int

    class Config:
        from_attributes = True
