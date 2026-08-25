from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class EarningResponse(BaseModel):
    id: str
    deposit_id: str
    amount: float
    day_number: int
    status: str
    claimed_at: Optional[datetime] = None
    due_date: datetime
    created_at: datetime
    package_name: Optional[str] = None

    class Config:
        from_attributes = True


class DailyEarningClaim(BaseModel):
    deposit_id: str


class EarningSummary(BaseModel):
    today_earning: float = 0
    earning_claimed: bool = False
    total_earnings: float = 0
    unclaimed_days: int = 0