import os
import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.core.deps import get_current_user, get_current_admin
from app.models.user import User
from app.models.feedback import Feedback, FeedbackLove

router = APIRouter(prefix="/feedback", tags=["Feedback"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/create")
async def create_feedback(
    message: str = Form(None),
    image: UploadFile = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not message and not image:
        raise HTTPException(status_code=400, detail="Provide a message or an image")

    image_path = None
    if image:
        ext = os.path.splitext(image.filename)[1] if image.filename else ".jpg"
        filename = f"{uuid.uuid4()}{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        content = await image.read()
        with open(filepath, "wb") as f:
            f.write(content)
        image_path = f"/uploads/{filename}"

    feedback = Feedback(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        message=message,
        image_path=image_path,
        love_count=0,
        status="unread",
    )

    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    return {
        "success": True,
        "message": "Posted successfully",
        "feedback": format_feedback(feedback, current_user.id, db),
    }


@router.get("/feed")
def get_feed(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    feedbacks = (
        db.query(Feedback)
        .order_by(Feedback.created_at.desc())
        .all()
    )

    return {
        "success": True,
        "feedbacks": [format_feedback(f, current_user.id, db) for f in feedbacks],
    }


@router.post("/love/{feedback_id}")
def toggle_love(
    feedback_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if not feedback:
        raise HTTPException(status_code=404, detail="Post not found")

    existing = (
        db.query(FeedbackLove)
        .filter(
            FeedbackLove.user_id == current_user.id,
            FeedbackLove.feedback_id == feedback_id,
        )
        .first()
    )

    if existing:
        db.delete(existing)
        feedback.love_count = max(0, (feedback.love_count or 0) - 1)
        db.commit()
        return {"success": True, "loved": False, "love_count": feedback.love_count}
    else:
        love = FeedbackLove(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            feedback_id=feedback_id,
        )
        db.add(love)
        feedback.love_count = (feedback.love_count or 0) + 1
        db.commit()
        return {"success": True, "loved": True, "love_count": feedback.love_count}


@router.get("/my-feedback")
def get_my_feedback(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    feedbacks = (
        db.query(Feedback)
        .filter(Feedback.user_id == current_user.id)
        .order_by(Feedback.created_at.desc())
        .all()
    )

    return {
        "success": True,
        "feedbacks": [format_feedback(f, current_user.id, db) for f in feedbacks],
    }


@router.get("/all")
def get_all_feedback(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    feedbacks = (
        db.query(Feedback)
        .order_by(Feedback.created_at.desc())
        .all()
    )

    return {
        "success": True,
        "feedbacks": [format_feedback(f, f.user_id, db) for f in feedbacks],
    }


def format_feedback(feedback, current_user_id, db):
    has_loved = (
        db.query(FeedbackLove)
        .filter(
            FeedbackLove.user_id == current_user_id,
            FeedbackLove.feedback_id == feedback.id,
        )
        .first()
    ) is not None

    phone = feedback.user.phone if feedback.user else "Unknown"
    masked = phone[:3] + "****" + phone[-2:] if len(phone) >= 5 else phone

    return {
        "id": feedback.id,
        "user_id": feedback.user_id,
        "user_display": masked,
        "message": feedback.message,
        "image_path": feedback.image_path,
        "love_count": feedback.love_count or 0,
        "has_loved": has_loved,
        "created_at": feedback.created_at.isoformat(),
    }