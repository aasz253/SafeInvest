from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ReferralResponse(BaseModel):
    id: str
    phone: str
    full_name: Optional[str] = None
    deposit_amount: float = 0
    bonus_amount: float = 0
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class ReferralBonusResponse(BaseModel):
    total_bonus: float = 0
    invitee_count: int = 0
    bonuses: List[ReferralResponse] = []


class ReferralCodeResponse(BaseModel):
    referral_code: str
    referral_link: str