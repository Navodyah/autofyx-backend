# models/profile_models.py
from pydantic import BaseModel, Field, validator
from typing import Optional, Literal


class UserProfileUpdate(BaseModel):
    monthly_income: Optional[float] = Field(None, ge=0)
    purpose: Optional[Literal["daily_commute", "family", "performance", "luxury"]] = None
    area: Optional[Literal["city", "highway", "mixed", "off-road"]] = None
    fuel_pref: Optional[str] = None
    transmission_pref: Optional[str] = None
    max_comb_l_per_100: Optional[float] = Field(None, gt=0)
    vehicle_class_pref: Optional[str] = None

    # Personal information
    phone_number: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = Field(default="Sri Lanka")

    # Preferences
    notification_enabled: Optional[bool] = True
    email_updates: Optional[bool] = True


class BasicInfoUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[str] = None


class PasswordChange(BaseModel):
    current_password: str = Field(..., min_length=6)
    new_password: str = Field(..., min_length=6)
    confirm_password: str = Field(..., min_length=6)

    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v
