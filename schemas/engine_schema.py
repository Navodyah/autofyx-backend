from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal


class EngineTypeBase(BaseModel):
    engine_type_name: str
    cylinders: int = Field(..., ge=1, le=16)



# No engine_type_id required when creating; DB will generate it
class EngineTypeCreate(EngineTypeBase):
    pass


class EngineTypeUpdate(BaseModel):
    engine_type_name: Optional[str] = None
    cylinders: Optional[int] = Field(None, ge=1, le=16)



class EngineTypeResponse(EngineTypeBase):
    engine_type_id: int

    class Config:
        from_attributes = True
