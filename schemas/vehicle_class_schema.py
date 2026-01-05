from pydantic import BaseModel


class VehicleClassBase(BaseModel):
    class_name: str


class VehicleClassCreate(VehicleClassBase):
    pass


class VehicleClassUpdate(VehicleClassBase):
    pass


class VehicleClassResponse(VehicleClassBase):
    class_id: int

    class Config:
        from_attributes = True
