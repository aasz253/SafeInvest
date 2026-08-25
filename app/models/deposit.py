import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Numeric, ForeignKey
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base


class DepositStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Deposit(Base):
    __tablename__ = "deposits"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    package_id = Column(String(36), ForeignKey("packages.id"), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    status = Column(String(20), default=DepositStatus.PENDING.value, nullable=False)
    reference = Column(String(100), unique=True, nullable=False, index=True)
    payment_method = Column(String(50), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    rejected_reason = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="deposits")
    package = relationship("Package")
    earnings = relationship("Earning", back_populates="deposit")
    referral_bonuses = relationship("ReferralBonus", back_populates="deposit")