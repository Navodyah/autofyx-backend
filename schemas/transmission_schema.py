from pydantic import BaseModel
from typing import Optional


class TransmissionBase(BaseModel):
    transmission_name: str
    category: Optional[str] = None


class TransmissionCreate(TransmissionBase):
    pass


class TransmissionUpdate(BaseModel):
    transmission_name: Optional[str] = None
    category: Optional[str] = None


class TransmissionResponse(TransmissionBase):
    transmission_id: int

    class Config:
        from_attributes = True
