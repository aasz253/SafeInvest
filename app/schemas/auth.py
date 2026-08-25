from pydantic import BaseModel, Field
from typing import Optional


class UserRegister(BaseModel):
    phone: str = Field(..., pattern=r"^(\+?254|0)[17]\d{8}$")
    password: str = Field(..., min_length=8)
    referral_code: Optional[str] = None


class UserLogin(BaseModel):
    phone: str = Field(..., pattern=r"^(\+?254|0)[17]\d{8}$")
    password: str


class OTPVerify(BaseModel):
    phone: str = Field(..., pattern=r"^(\+?254|0)[17]\d{8}$")
    otp: str = Field(..., pattern=r"^\d{6}$")


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[str] = None