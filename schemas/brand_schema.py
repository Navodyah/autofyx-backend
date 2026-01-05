from pydantic import BaseModel
from typing import Optional


class BrandBase(BaseModel):
    brand_name: str
    country: Optional[str] = None


class BrandCreate(BaseModel):
    brand_id: int
    brand_name: str
    country: Optional[str] = None



class BrandUpdate(BaseModel):
    brand_name: Optional[str] = None
    country: Optional[str] = None


class BrandResponse(BrandBase):
    brand_id: int

    class Config:
        from_attributes = True
