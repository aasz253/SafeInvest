import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Numeric, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class GiftCode(Base):
    __tablename__ = "gift_codes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String(20), unique=True, nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    description = Column(String(200), nullable=True)
    is_active = Column(Boolean, default=True)
    created_by_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    used_by_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    used_at = Column(DateTime, nullable=True)

    created_by = relationship("User", foreign_keys=[created_by_id])
    used_by = relationship("User", foreign_keys=[used_by_id])