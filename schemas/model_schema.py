from pydantic import BaseModel
from typing import Optional

class ModelCreate(BaseModel):
    brand_id: int
    model_name: str
    start_year: Optional[int] = None
    end_year: Optional[int] = None

class ModelUpdate(BaseModel):
    brand_id: Optional[int] = None
    model_name: Optional[str] = None
    start_year: Optional[int] = None
    end_year: Optional[int] = None

class ModelResponse(BaseModel):
    model_id: int
    brand_id: Optional[int] = None  # Allow NULL brand_id
    model_name: str
    start_year: Optional[int] = None
    end_year: Optional[int] = None

    class Config:
        from_attributes = True
