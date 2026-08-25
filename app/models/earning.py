import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Numeric, Integer, ForeignKey
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base


class EarningStatus(str, enum.Enum):
    PENDING = "pending"
    CLAIMED = "claimed"


class Earning(Base):
    __tablename__ = "earnings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    deposit_id = Column(String(36), ForeignKey("deposits.id"), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    day_number = Column(Integer, nullable=False)
    status = Column(String(20), default=EarningStatus.PENDING.value, nullable=False)
    claimed_at = Column(DateTime, nullable=True)
    due_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="earnings")
    deposit = relationship("Deposit", back_populates="earnings")