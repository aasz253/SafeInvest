from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_admin
from app.models.user import User
from app.models.deposit import Deposit, DepositStatus
from app.models.earning import Earning, EarningStatus
from app.models.admin_log import AdminLog
from app.services.deposit_service import DepositService

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/users")
def get_all_users(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    users = db.query(User).all()
    
    return {
        "success": True,
        "users": [
            {
                "id": str(u.id),
                "phone": u.phone,
                "full_name": u.full_name,
                "referral_code": u.referral_code,
                "is_verified": u.is_verified,
                "is_admin": u.is_admin,
                "created_at": u.created_at.isoformat(),
            }
            for u in users
        ],
    }


@router.get("/deposits")
def get_all_deposits(
    status: str = None,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    query = db.query(Deposit)
    if status:
        query = query.filter(Deposit.status == status)
    deposits = query.all()
    
    return {
        "success": True,
        "deposits": [
            {
                "id": str(d.id),
                "user_id": str(d.user_id),
                "user_phone": d.user.phone,
                "package_name": d.package.name,
                "amount": float(d.amount),
                "status": d.status,
                "reference": d.reference,
                "created_at": d.created_at.isoformat(),
            }
            for d in deposits
        ],
    }


@router.get("/earnings")
def get_all_earnings(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    earnings = db.query(Earning).all()
    
    return {
        "success": True,
        "earnings": [
            {
                "id": str(e.id),
                "user_id": str(e.user_id),
                "user_phone": e.user.phone,
                "amount": float(e.amount),
                "day_number": e.day_number,
                "status": e.status,
                "claimed_at": e.claimed_at.isoformat() if e.claimed_at else None,
                "due_date": e.due_date.isoformat(),
            }
            for e in earnings
        ],
    }


@router.get("/reports")
def get_reports(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    total_users = db.query(User).count()
    total_deposits = db.query(Deposit).filter(Deposit.status == DepositStatus.APPROVED.value).count()
    total_earnings = db.query(Earning).filter(Earning.status == EarningStatus.CLAIMED.value).count()
    pending_deposits = db.query(Deposit).filter(Deposit.status == DepositStatus.PENDING.value).count()
    
    total_users_with_active = (
        db.query(User)
        .join(Deposit)
        .filter(Deposit.status == DepositStatus.APPROVED.value)
        .count()
    )
    
    return {
        "success": True,
        "reports": {
            "total_users": total_users,
            "users_with_active_deposits": total_users_with_active,
            "total_deposits_approved": total_deposits,
            "pending_deposits": pending_deposits,
            "total_earnings_claimed": total_earnings,
        },
    }