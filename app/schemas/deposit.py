from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class DepositCreate(BaseModel):
    package_id: str
    amount: float = Field(..., gt=0)
    payment_method: str = Field(default="manual")


class DepositResponse(BaseModel):
    id: str
    user_id: str
    package_id: str
    amount: float
    status: str
    reference: str
    payment_method: Optional[str] = None
    approved_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    rejected_reason: Optional[str] = None
    created_at: datetime
    package_name: Optional[str] = None

    class Config:
        from_attributes = True


class AdminDepositAction(BaseModel):
    action: str = Field(..., pattern=r"^(approve|reject)$")
    reason: Optional[str] = None