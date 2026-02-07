from __future__ import annotations

from typing import Optional, List
from pydantic import BaseModel, Field


class RecommendRequest(BaseModel):
    # Income inputs (either one)
    monthly_income: Optional[float] = Field(None, ge=0, description="Monthly income in LKR")
    salary_level: Optional[str] = Field(
        None, description="Optional override: low|medium|high|luxury"
    )

    # Need-based inputs
    purpose: str = Field("daily_commute", description="daily_commute|family|performance|luxury")
    area: str = Field("mixed", description="city|highway|mixed|off-road")

    # Optional hard filters (DB-side)
    fuel: Optional[str] = Field(None, description="Example: 'X - Regular Gasoline' / 'D - Diesel' / 'Z - Premium Gasoline'")
    transmission: Optional[str] = Field(None, description="Example: 'A=Automatic' / 'Manual' / 'Any' / 'A6'")
    max_comb_l_per_100: Optional[float] = Field(None, gt=0, description="Max combined fuel consumption (L/100km)")
    vehicle_class: Optional[str] = Field(None, description="Exact class name to force (e.g., COMPACT)")

    # Output controls
    top_n: int = Field(10, ge=1, le=50)
    candidate_limit: int = Field(2000, ge=100, le=20000)


class VehicleRecItem(BaseModel):
    vehicle_id: Optional[int] = None

    YEAR: Optional[int] = None
    MAKE: Optional[str] = None
    MODEL: Optional[str] = None
    VEHICLE_CLASS: Optional[str] = Field(None, alias="VEHICLE CLASS")

    ENGINE_SIZE: Optional[float] = Field(None, alias="ENGINE SIZE")
    CYLINDERS: Optional[float] = None
    TRANSMISSION: Optional[str] = None
    FUEL: Optional[str] = None

    COMB_L_100: Optional[float] = Field(None, alias="COMB (L/100 km)")
    COMB_MPG: Optional[float] = Field(None, alias="COMB (mpg)")
    EMISSIONS: Optional[float] = None

    Compatibility_Score: Optional[float] = None
    Need_Match: Optional[float] = None
    Usage_Match: Optional[float] = None


class RecommendResponse(BaseModel):
    message: Optional[str] = None
    count: int = 0
    items: List[dict] = []
