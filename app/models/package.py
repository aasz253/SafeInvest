import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Numeric, Integer
from app.core.database import Base


class Package(Base):
    __tablename__ = "packages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(50), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    daily_bonus = Column(Numeric(12, 2), nullable=True)
    duration_days = Column(Integer, nullable=True)
    total_return = Column(Numeric(12, 2), nullable=True)
    is_increasing = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    description = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)