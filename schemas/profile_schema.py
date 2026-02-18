from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field, conint, confloat

SalaryLevel = Literal["low", "medium", "high", "luxury"]
Purpose = Literal["daily_commute", "family", "performance", "luxury"]
Area = Literal["city", "highway", "mixed", "off-road"]


def income_to_salary_level(monthly_income: Optional[float]) -> Optional[SalaryLevel]:
    if monthly_income is None:
        return None
    if monthly_income < 150000:
        return "low"
    if 150000 <= monthly_income <= 600000:
        return "medium"
    if 600000 < monthly_income < 1000000:
        return "high"
    return "luxury"


class UserProfileBase(BaseModel):
    monthly_income: Optional[confloat(ge=0)] = None
    salary_level: Optional[SalaryLevel] = None  # optional override

    purpose: Purpose = "daily_commute"
    area: Area = "mixed"

    fuel_pref: Optional[str] = None  # ex: "X - Regular Gasoline"
    transmission_pref: Optional[str] = None  # ex: "A=Automatic"
    max_comb_l_per_100: Optional[confloat(gt=0)] = None  # ex: 10

    # extra options if needed later
    vehicle_class_pref: Optional[str] = None

    class Config:
        extra = "ignore"


class UserProfileUpdate(UserProfileBase):
    # Update payload - all optional (PATCH style)
    purpose: Optional[Purpose] = None
    area: Optional[Area] = None


class UserProfileOut(UserProfileBase):
    user_id: str
    effective_salary_level: Optional[SalaryLevel] = None

    created_at: Optional[str] = None
    updated_at: Optional[str] = None
