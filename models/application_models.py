from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class ResearcherApplicationCreate(BaseModel):
    name: str
    email: EmailStr
    academic_role: str
    comment: Optional[str] = None
    appwrite_id: str

class ResearcherApplicationUpdateStatus(BaseModel):
    status: str
