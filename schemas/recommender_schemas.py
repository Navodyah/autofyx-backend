from __future__ import annotations

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field


SalaryLevel = Literal["low", "medium", "high", "luxury"]


class RecommendRequest(BaseModel):
    # Income inputs
    monthly_income: Optional[float] = Field(None, ge=0, description="Monthly income in LKR")
    salary_level: Optional[SalaryLevel] = Field(
        None, description="Optional override: low|medium|high|luxury"
    )

    # Main preferences
    purpose: str = Field("daily_commute", description="daily_commute|family|performance|luxury")
    area: str = Field("mixed", description="city|highway|mixed|off-road")

    # Optional DB hard filters
    fuel: Optional[str] = Field(None, description="Example: 'D - Diesel' / 'X - Regular Gasoline' / 'Z - Premium Gasoline'")
    transmission: Optional[str] = Field(None, description="Example: 'A=Automatic' / 'Manual' / 'Any' / 'A6'")
    max_comb_l_per_100: Optional[float] = Field(None, gt=0, description="Max combined fuel consumption (L/100km)")
    vehicle_class: Optional[str] = Field(None, description="Exact class name (e.g., COMPACT)")

    # Output controls
    top_n: int = Field(10, ge=1, le=50)
    candidate_limit: int = Field(2000, ge=100, le=20000)


class RecommendResponse(BaseModel):
    message: Optional[str] = None
    count: int = 0
    items: List[Dict[str, Any]] = []
