from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from pydantic import Field

class User(BaseModel):
    username: str
    email: EmailStr
    password: str
    user_type: str = Field(default="user")
    appwrite_id: Optional[str] = None

    @field_validator('user_type')
    @classmethod
    def validate_user_type(cls, v):
        allowed = ["user", "admin", "researcher"]
        v_lower = v.lower().strip()  # Handle case and whitespace
        if v_lower not in allowed:
            raise ValueError(f"user_type must be one of {allowed}, got '{v}'")
        return v_lower

    @field_validator('appwrite_id')
    @classmethod
    def normalize_appwrite_id(cls, value: Optional[str]):
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

class UserLogin(BaseModel):
    email: EmailStr
    password: str
