from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal


class EngineTypeBase(BaseModel):
    engine_type_name: str
    cylinders: int = Field(..., ge=1, le=16)
    engine_size: Decimal = Field(..., ge=0, decimal_places=1)


class EngineTypeCreate(EngineTypeBase):
    engine_type_id: int


class EngineTypeUpdate(BaseModel):
    engine_type_name: Optional[str] = None
    cylinders: Optional[int] = Field(None, ge=1, le=16)
    engine_size: Optional[Decimal] = Field(None, ge=0, decimal_places=1)


class EngineTypeResponse(EngineTypeBase):
    engine_type_id: int

    class Config:
        from_attributes = True
