from pydantic import BaseModel


class FuelTypeBase(BaseModel):
    fuel_type_name: str


class FuelTypeCreate(FuelTypeBase):
    fuel_type_id: int


class FuelTypeUpdate(FuelTypeBase):
    pass


class FuelTypeResponse(FuelTypeBase):
    fuel_type_id: int

    class Config:
        from_attributes = True
