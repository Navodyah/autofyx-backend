from pydantic import BaseModel
from typing import Optional


class OilQualityBase(BaseModel):
    oil_grade: str
    description: Optional[str] = None


class OilQualityCreate(OilQualityBase):
    pass


class OilQualityUpdate(BaseModel):
    oil_grade: Optional[str] = None
    description: Optional[str] = None


class OilQualityResponse(OilQualityBase):
    oil_id: int

    class Config:
        from_attributes = True
