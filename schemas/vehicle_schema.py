from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal
from datetime import datetime


class VehicleBase(BaseModel):
    model_id: int
    class_id: int
    engine_type_id: int
    fuel_type_id: int
    transmission_id: int
    oil_id: int
    tyre_size: Optional[str] = None
    fuel_efficiency_highway: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    fuel_efficiency_combined: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    description: Optional[str] = None


class VehicleCreate(VehicleBase):
    pass


class VehicleUpdate(BaseModel):
    model_id: Optional[int] = None
    class_id: Optional[int] = None
    engine_type_id: Optional[int] = None
    fuel_type_id: Optional[int] = None
    transmission_id: Optional[int] = None
    oil_id: Optional[int] = None
    tyre_size: Optional[str] = None
    fuel_efficiency_highway: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    fuel_efficiency_combined: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    description: Optional[str] = None


class VehicleResponse(VehicleBase):
    vehicle_id: int
    created_at: datetime

    class Config:
        from_attributes = True
