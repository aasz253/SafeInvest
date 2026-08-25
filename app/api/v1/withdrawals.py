from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from datetime import datetime
from app.core.database import get_db
from app.core.deps import get_current_user, get_current_admin
from app.models.user import User
from app.models.deposit import Deposit
from app.models.earning import Earning
from app.models.withdrawal import Withdrawal

router = APIRouter(prefix="/withdrawals", tags=["Withdrawals"])


class WithdrawalCreate(BaseModel):
    amount: float
    phone: str


class WithdrawalAction(BaseModel):
    reason: str = ""


def get_user_balance(db: Session, user_id: str) -> float:
    total_deposited = float(db.query(func.coalesce(func.sum(Deposit.amount), 0)).filter(
        Deposit.user_id == user_id, Deposit.status == "approved"
    ).scalar() or 0)

    total_withdrawn = float(db.query(func.coalesce(func.sum(Withdrawal.amount), 0)).filter(
        Withdrawal.user_id == user_id, Withdrawal.status.in_(["approved", "pending"])
    ).scalar() or 0)

    total_earned = float(db.query(func.coalesce(func.sum(Earning.amount), 0)).filter(
        Earning.user_id == user_id, Earning.status == "claimed"
    ).scalar() or 0)

    total_gifts = 0.0
    from app.models.gift_code import GiftCode
    gifts = db.query(GiftCode).filter(
        GiftCode.used_by_id == user_id, GiftCode.is_active == True
    ).all()
    for g in gifts:
        total_gifts += float(g.amount)

    from app.models.referral import ReferralBonus
    referral_bonuses = float(db.query(func.coalesce(func.sum(ReferralBonus.amount), 0)).filter(
        ReferralBonus.inviter_id == user_id
    ).scalar() or 0)

    balance = total_deposited - total_withdrawn + total_earned + total_gifts + referral_bonuses
    return balance


@router.post("/create")
def create_withdrawal(
    data: WithdrawalCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if data.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be greater than 0")

    if not data.phone or len(data.phone.strip()) < 10:
        raise HTTPException(status_code=400, detail="Enter a valid phone number")

    balance = get_user_balance(db, current_user.id)
    if data.amount > balance:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient balance. Your balance is KES {balance:.0f}",
        )

    withdrawal = Withdrawal(
        id=str(__import__("uuid").uuid4()),
        user_id=current_user.id,
        amount=data.amount,
        phone=data.phone.strip(),
        status="pending",
        created_at=datetime.utcnow(),
    )
    db.add(withdrawal)
    db.commit()

    return {
        "success": True,
        "message": f"Withdrawal request of KES {data.amount:.0f} submitted. Waiting for admin approval.",
        "request": {
            "id": str(withdrawal.id),
            "amount": float(withdrawal.amount),
            "phone": withdrawal.phone,
            "status": withdrawal.status,
            "created_at": withdrawal.created_at.isoformat(),
        },
    }


@router.get("/my-requests")
def my_withdrawals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    requests = (
        db.query(Withdrawal)
        .filter(Withdrawal.user_id == current_user.id)
        .order_by(Withdrawal.created_at.desc())
        .all()
    )

    return {
        "success": True,
        "requests": [
            {
                "id": str(r.id),
                "amount": float(r.amount),
                "phone": r.phone,
                "status": r.status,
                "reason": r.reason,
                "created_at": r.created_at.isoformat(),
                "reviewed_at": r.reviewed_at.isoformat() if r.reviewed_at else None,
            }
            for r in requests
        ],
    }


@router.get("/balance")
def my_balance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    balance = get_user_balance(db, current_user.id)
    return {"success": True, "balance": balance}


@router.get("/admin/list")
def admin_list_withdrawals(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    requests = (
        db.query(Withdrawal)
        .order_by(Withdrawal.created_at.desc())
        .all()
    )

    return {
        "success": True,
        "requests": [
            {
                "id": str(r.id),
                "user_phone": r.user.phone,
                "amount": float(r.amount),
                "phone": r.phone,
                "status": r.status,
                "reason": r.reason,
                "created_at": r.created_at.isoformat(),
                "reviewed_at": r.reviewed_at.isoformat() if r.reviewed_at else None,
            }
            for r in requests
        ],
    }


@router.put("/admin/approve/{request_id}")
def admin_approve_withdrawal(
    request_id: str,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    request = db.query(Withdrawal).filter(Withdrawal.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Withdrawal request not found")
    if request.status != "pending":
        raise HTTPException(status_code=400, detail="Request already processed")

    request.status = "approved"
    request.reviewed_at = datetime.utcnow()
    request.reviewed_by_id = admin.id
    db.commit()

    return {
        "success": True,
        "message": f"Withdrawal of KES {float(request.amount)} approved for {request.user.phone}",
    }


@router.put("/admin/reject/{request_id}")
def admin_reject_withdrawal(
    request_id: str,
    data: WithdrawalAction,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    request = db.query(Withdrawal).filter(Withdrawal.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Withdrawal request not found")
    if request.status != "pending":
        raise HTTPException(status_code=400, detail="Request already processed")

    request.status = "rejected"
    request.reason = data.reason
    request.reviewed_at = datetime.utcnow()
    request.reviewed_by_id = admin.id
    db.commit()

    return {
        "success": True,
        "message": f"Withdrawal rejected",
    }
