from pydantic import BaseModel
from typing import Optional


class PackageResponse(BaseModel):
    id: str
    name: str
    amount: float
    daily_bonus: Optional[float] = None
    duration_days: Optional[int] = None
    total_return: Optional[float] = None
    is_increasing: bool = False
    description: Optional[str] = None
    is_active: bool = True

    class Config:
        from_attributes = True