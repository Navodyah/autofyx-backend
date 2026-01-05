from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal
from datetime import date


class MaintenanceCostBase(BaseModel):
    vehicle_id: int
    yearly_cost: Decimal = Field(..., ge=0, decimal_places=2)
    recorded_date: date
    source: Optional[str] = None


class MaintenanceCostCreate(MaintenanceCostBase):
    pass


class MaintenanceCostUpdate(BaseModel):
    vehicle_id: Optional[int] = None
    yearly_cost: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    recorded_date: Optional[date] = None
    source: Optional[str] = None


class MaintenanceCostResponse(MaintenanceCostBase):
    record_id: int

    class Config:
        from_attributes = True
