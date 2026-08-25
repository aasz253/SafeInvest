import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime
from app.core.database import Base


class AdminSetting(Base):
    __tablename__ = "admin_settings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(String(500), nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
