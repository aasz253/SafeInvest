from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class FeedbackCreate(BaseModel):
    message: str


class FeedbackResponse(BaseModel):
    id: str
    user_id: str
    message: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True