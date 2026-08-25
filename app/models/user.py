import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    phone = Column(String(20), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    referral_code = Column(String(20), unique=True, nullable=False, index=True)
    invited_by_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    otp_code = Column(String(6), nullable=True)
    otp_expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    invited_by = relationship("User", remote_side=[id], backref="invitees")
    deposits = relationship("Deposit", back_populates="user")
    earnings = relationship("Earning", back_populates="user")
    referral_bonuses_given = relationship("ReferralBonus", foreign_keys="ReferralBonus.inviter_id", back_populates="inviter")
    referral_bonuses_received = relationship("ReferralBonus", foreign_keys="ReferralBonus.invitee_id", back_populates="invitee")
    feedback = relationship("Feedback", back_populates="user")
    feedback_loves = relationship("FeedbackLove", back_populates="user")
    admin_logs = relationship("AdminLog", back_populates="admin")