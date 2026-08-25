from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class UserBase(BaseModel):
    phone: str
    full_name: Optional[str] = None
    referral_code: str
    is_active: bool
    is_admin: bool
    is_verified: bool


class UserCreate(BaseModel):
    phone: str
    password: str
    referral_code: Optional[str] = None


class UserResponse(UserBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True


class UserProfile(UserResponse):
    total_earnings: float = 0
    referral_bonus: float = 0
    active_packages_count: int = 0
    total_invites: int = 0