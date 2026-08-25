import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class DepositRequest(Base):
    __tablename__ = "deposit_requests"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    mpesa_message = Column(Text, nullable=False)
    status = Column(String(20), default="pending", nullable=False)
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", foreign_keys=[user_id], backref="deposit_requests")
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_id])
