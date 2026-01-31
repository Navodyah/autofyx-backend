from pydantic import BaseModel


class FuelTypeBase(BaseModel):
    fuel_type_name: str


# Do not require fuel_type_id when creating; DB will generate it
class FuelTypeCreate(FuelTypeBase):
    pass


class FuelTypeUpdate(FuelTypeBase):
    pass


class FuelTypeResponse(FuelTypeBase):
    fuel_type_id: int

    class Config:
        from_attributes = True




