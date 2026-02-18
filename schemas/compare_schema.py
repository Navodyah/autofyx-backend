from pydantic import BaseModel
from typing import List

class VehicleCompareItem(BaseModel):
    make: str
    model: str

class VehicleCompareRequest(BaseModel):
    vehicles: List[VehicleCompareItem]

class VehicleCompareResponse(BaseModel):
    count: int
    items: list[dict]
