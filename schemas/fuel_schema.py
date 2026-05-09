from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class FuelTypeBase(BaseModel):
    fuel_type_name: str
    fuel_price: Optional[Decimal] = None


# Do not require fuel_type_id when creating; DB will generate it
class FuelTypeCreate(FuelTypeBase):
    pass


class FuelTypeUpdate(FuelTypeBase):
    pass


class FuelTypeResponse(FuelTypeBase):
    fuel_type_id: int
    fuel_efficiency_combined: Optional[Decimal] = None
    last_updated: Optional[str] = None

    class Config:
        from_attributes = True

