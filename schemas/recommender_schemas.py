from __future__ import annotations

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field


SalaryLevel = Literal["low", "medium_low", "medium", "high", "luxury"]


class RecommendRequest(BaseModel):
    # Financial inputs (salary is required)
    salary: float = Field(..., gt=0, description="Monthly salary in LKR (required)")
    rate_of_interest: Optional[float] = Field(None, ge=0, description="Annual interest rate in percent. Defaults to 13.")
    number_of_months: Optional[int] = Field(None, gt=0, description="Loan tenure in months. Defaults to 60.")
    down_payment_amount: Optional[float] = Field(None, ge=0, description="Down payment in LKR (absolute amount). If provided, overrides down_payment_ratio.")
    down_payment_ratio: Optional[float] = Field(None, ge=0, le=1, description="Down payment as ratio of vehicle price. Defaults to 0.5 (50%). Used only if down_payment_amount is not provided.")

    # Backward compatibility
    monthly_income: Optional[float] = Field(None, ge=0, description="Deprecated: use salary")
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
    vehicle_class: Optional[str] = Field(None, description="Single class override (e.g. COMPACT). Use vehicle_classes for multi-class frontend filtering.")
    vehicle_classes: Optional[List[str]] = Field(
        None,
        description="Pre-computed final class list from frontend (salary ∩ purpose × area). When provided, used directly as the DB class filter — skips all internal mapper logic."
    )

    # Sri Lanka market: maintainability preference
    # 'high'    → strongly prioritise low-maintenance vehicles (Japanese/Korean Kei to compact)
    # 'average' → moderate background weight (default when not provided)
    # 'none'    → no maintainability bias (high-income user-driven)
    maintainability_priority: Optional[Literal["high", "average", "none"]] = Field(
        None,
        description="Maintainability preference: 'high' (Japanese/Korean compact), 'average' (default), 'none' (no bias)"
    )

    # Output controls
    top_n: int = Field(10, ge=1, le=50)
    candidate_limit: int = Field(2000, ge=100, le=20000)


class RecommendResponse(BaseModel):
    message: Optional[str] = None
    count: int = 0
    items: List[Dict[str, Any]] = Field(default_factory=list)
    finance: Dict[str, Any] = Field(default_factory=dict)
