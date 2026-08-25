from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.earning import DailyEarningClaim
from app.services.earning_service import EarningService

router = APIRouter(prefix="/earnings", tags=["Earnings"])


@router.get("/daily")
def get_daily_earning(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = EarningService(db)
    result = service.get_today_earning(current_user)
    return {"success": True, **result}


@router.post("/claim")
def claim_daily_earning(
    data: DailyEarningClaim,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        service = EarningService(db)
        result = service.claim_daily(user=current_user, deposit_id=str(data.deposit_id))
        return {"success": True, **result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/history")
def get_earning_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = EarningService(db)
    earnings = service.get_earning_history(current_user)
    
    return {
        "success": True,
        "earnings": [
            {
                "id": str(e.id),
                "amount": float(e.amount),
                "day_number": e.day_number,
                "status": e.status.value,
                "claimed_at": e.claimed_at.isoformat() if e.claimed_at else None,
                "due_date": e.due_date.isoformat(),
                "created_at": e.created_at.isoformat(),
            }
            for e in earnings
        ],
    }


@router.get("/summary")
def get_earning_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = EarningService(db)
    summary = service.get_earning_summary(current_user)
    return {"success": True, **summary}