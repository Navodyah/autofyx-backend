# python
# File: `schemas/vehicle_schema.py`
from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal
from datetime import datetime


class VehicleBase(BaseModel):
    model_name: Optional[str] = Field(None, alias="vehicle_model")
    brand_id: Optional[int] = None
    class_id: int
    engine_type_id: int
    fuel_type_id: int
    transmission_id: int
    oil_id: int
    engine_size: Optional[Decimal] = Field(None, ge=0)
    manufacturing_year: Optional[int] = None
    tyre_size: Optional[str] = None
    fuel_efficiency_highway: Optional[Decimal] = Field(None, ge=0)
    fuel_efficiency_combined: Optional[Decimal] = Field(None, ge=0)
    description: Optional[str] = None

    class Config:
        allow_population_by_field_name = True


class VehicleCreate(VehicleBase):
    model_name: str = Field(..., alias="vehicle_model")
    manufacturing_year: int

    class Config:
        allow_population_by_field_name = True


class VehicleUpdate(BaseModel):
    model_name: Optional[str] = Field(None, alias="vehicle_model")
    brand_id: Optional[int] = None
    class_id: Optional[int] = None
    engine_type_id: Optional[int] = None
    fuel_type_id: Optional[int] = None
    transmission_id: Optional[int] = None
    oil_id: Optional[int] = None
    engine_size: Optional[Decimal] = Field(None, ge=0)
    manufacturing_year: Optional[int] = None
    tyre_size: Optional[str] = None
    fuel_efficiency_highway: Optional[Decimal] = Field(None, ge=0)
    fuel_efficiency_combined: Optional[Decimal] = Field(None, ge=0)
    description: Optional[str] = None

    class Config:
        allow_population_by_field_name = True


class VehicleResponse(VehicleBase):
    vehicle_id: int
    created_at: datetime

    class Config:
        from_attributes = True
        allow_population_by_field_name = True
