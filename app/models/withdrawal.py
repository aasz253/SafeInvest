from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from app.models.base import Base
from datetime import datetime


class Withdrawal(Base):
    __tablename__ = "withdrawals"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    phone = Column(String(20), nullable=False)
    status = Column(String(20), default="pending")  # pending, approved, rejected
    reason = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by_id = Column(String(36), ForeignKey("users.id"), nullable=True)
