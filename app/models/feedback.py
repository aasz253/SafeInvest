import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer
from sqlalchemy.orm import relationship
from app.core.database import Base


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=True)
    image_path = Column(String(500), nullable=True)
    love_count = Column(Integer, default=0)
    status = Column(String(20), default="unread", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="feedback")
    loves = relationship("FeedbackLove", back_populates="feedback")


class FeedbackLove(Base):
    __tablename__ = "feedback_loves"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    feedback_id = Column(String(36), ForeignKey("feedback.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    feedback = relationship("Feedback", back_populates="loves")