import uuid
import random
import string
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.core.database import get_db
from app.core.deps import get_current_user, get_current_admin
from app.models.user import User
from app.models.gift_code import GiftCode

router = APIRouter(prefix="/gifts", tags=["Gifts"])


class GiftCodeCreate(BaseModel):
    amount: float
    description: Optional[str] = None
    quantity: int = 1


class GiftCodeRedeem(BaseModel):
    code: str


def generate_code(length=10):
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choices(chars, k=length))


@router.post("/admin/create")
def create_gift_codes(
    data: GiftCodeCreate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    codes = []
    for _ in range(min(data.quantity, 50)):
        code = generate_code()
        while db.query(GiftCode).filter(GiftCode.code == code).first():
            code = generate_code()

        gift = GiftCode(
            id=str(uuid.uuid4()),
            code=code,
            amount=data.amount,
            description=data.description,
            is_active=True,
            created_by_id=admin.id,
        )
        db.add(gift)
        codes.append(code)

    db.commit()

    return {
        "success": True,
        "message": f"{len(codes)} gift code(s) created",
        "codes": codes,
    }


@router.get("/admin/list")
def list_gift_codes(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    gifts = db.query(GiftCode).order_by(GiftCode.created_at.desc()).all()

    return {
        "success": True,
        "gifts": [
            {
                "id": g.id,
                "code": g.code,
                "amount": float(g.amount),
                "description": g.description,
                "is_active": g.is_active,
                "used_by": g.used_by.phone if g.used_by else None,
                "used_at": g.used_at.isoformat() if g.used_at else None,
                "created_at": g.created_at.isoformat(),
            }
            for g in gifts
        ],
    }


@router.put("/admin/toggle/{gift_id}")
def toggle_gift_code(
    gift_id: str,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    gift = db.query(GiftCode).filter(GiftCode.id == gift_id).first()
    if not gift:
        raise HTTPException(status_code=404, detail="Gift code not found")

    gift.is_active = not gift.is_active
    db.commit()

    return {
        "success": True,
        "message": f"Gift code {'activated' if gift.is_active else 'deactivated'}",
        "is_active": gift.is_active,
    }


@router.post("/redeem")
def redeem_gift_code(
    data: GiftCodeRedeem,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    code = data.code.strip().upper()
    gift = db.query(GiftCode).filter(GiftCode.code == code).first()

    if not gift:
        raise HTTPException(status_code=404, detail="Gift code not found")

    if not gift.is_active:
        raise HTTPException(status_code=400, detail="This code is inactive or voided")

    if gift.used_by_id:
        raise HTTPException(status_code=400, detail="This code has already been used")

    gift.used_by_id = current_user.id
    gift.used_at = datetime.utcnow()
    db.commit()

    return {
        "success": True,
        "message": f"You received KSH {float(gift.amount)}!",
        "amount": float(gift.amount),
        "description": gift.description,
    }


@router.get("/my-received")
def my_received_gifts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    gifts = (
        db.query(GiftCode)
        .filter(GiftCode.used_by_id == current_user.id)
        .order_by(GiftCode.used_at.desc())
        .all()
    )

    total = sum(float(g.amount) for g in gifts)

    return {
        "success": True,
        "total_received": total,
        "count": len(gifts),
        "gifts": [
            {
                "code": g.code,
                "amount": float(g.amount),
                "description": g.description,
                "received_at": g.used_at.isoformat() if g.used_at else None,
            }
            for g in gifts
        ],
    }