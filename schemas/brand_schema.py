from pydantic import BaseModel
from typing import Optional

class BrandCreate(BaseModel):
    brand_name: str
    country: Optional[str] = None

class BrandUpdate(BaseModel):
    brand_name: Optional[str] = None
    country: Optional[str] = None

class BrandResponse(BaseModel):
    brand_id: int
    brand_name: str
    country: Optional[str] = None

    class Config:
        from_attributes = True

