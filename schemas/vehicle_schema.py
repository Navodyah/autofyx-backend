# python
# File: `schemas/vehicle_schema.py`
from pydantic import BaseModel, Field, ConfigDict, root_validator
from typing import Optional
from decimal import Decimal
from datetime import datetime


class VehicleBase(BaseModel):
    model_name: Optional[str] = None
    brand_id: Optional[int] = None
    class_id: int
    engine_type_id: int
    fuel_type_id: int
    transmission_id: int
    oil_id: int
    engine_size: Optional[Decimal] = Field(None, ge=0)
    minimum_price: Optional[Decimal] = Field(None, ge=0)
    max_price: Optional[Decimal] = Field(None, ge=0)
    manufacturing_year: Optional[int] = None
    tyre_size: Optional[str] = None
    fuel_efficiency_highway: Optional[Decimal] = Field(None, ge=0)
    fuel_efficiency_combined: Optional[Decimal] = Field(None, ge=0)
    description: Optional[str] = None
    image_url: Optional[str] = None

    @root_validator(pre=True)
    def populate_model_name(cls, values):
        if isinstance(values, dict) and not values.get("model_name") and values.get("vehicle_model"):
            values["model_name"] = values["vehicle_model"]
        return values

    model_config = ConfigDict(validate_by_name=True)


class VehicleCreate(VehicleBase):
    model_name: str
    manufacturing_year: int


class VehicleUpdate(BaseModel):
    model_name: Optional[str] = None
    brand_id: Optional[int] = None
    class_id: Optional[int] = None
    engine_type_id: Optional[int] = None
    fuel_type_id: Optional[int] = None
    transmission_id: Optional[int] = None
    oil_id: Optional[int] = None
    engine_size: Optional[Decimal] = Field(None, ge=0)
    minimum_price: Optional[Decimal] = Field(None, ge=0)
    max_price: Optional[Decimal] = Field(None, ge=0)
    manufacturing_year: Optional[int] = None
    tyre_size: Optional[str] = None
    fuel_efficiency_highway: Optional[Decimal] = Field(None, ge=0)
    fuel_efficiency_combined: Optional[Decimal] = Field(None, ge=0)
    description: Optional[str] = None
    image_url: Optional[str] = None

    @root_validator(pre=True)
    def populate_model_name(cls, values):
        if isinstance(values, dict) and not values.get("model_name") and values.get("vehicle_model"):
            values["model_name"] = values["vehicle_model"]
        return values

    model_config = ConfigDict(validate_by_name=True)


class VehicleResponse(VehicleBase):
    vehicle_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, validate_by_name=True)
