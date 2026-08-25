import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Numeric, ForeignKey
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base


class BonusType(str, enum.Enum):
    INVITER = "inviter"
    INVITEE = "invitee"


class BonusStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"


class ReferralBonus(Base):
    __tablename__ = "referral_bonuses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    inviter_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    invitee_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    deposit_id = Column(String(36), ForeignKey("deposits.id"), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    bonus_type = Column(String(20), nullable=False)
    status = Column(String(20), default=BonusStatus.PENDING.value, nullable=False)
    paid_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    inviter = relationship("User", foreign_keys=[inviter_id], back_populates="referral_bonuses_given")
    invitee = relationship("User", foreign_keys=[invitee_id], back_populates="referral_bonuses_received")
    deposit = relationship("Deposit", back_populates="referral_bonuses")