from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user, get_current_admin
from app.models.user import User
from app.schemas.deposit import DepositCreate, AdminDepositAction
from app.services.deposit_service import DepositService

router = APIRouter(prefix="/deposits", tags=["Deposits"])


@router.post("/create")
def create_deposit(
    data: DepositCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        service = DepositService(db)
        result = service.create_deposit(
            user=current_user,
            package_id=data.package_id,
            amount=data.amount,
            payment_method=data.payment_method,
        )
        return {
            "success": True,
            "message": result["message"],
            "deposit": {
                "id": str(result["deposit"].id),
                "reference": result["deposit"].reference,
                "amount": float(result["deposit"].amount),
                "status": result["deposit"].status,
                "package_name": result["package"].name,
            },
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/pending")
def get_pending_deposits(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    service = DepositService(db)
    deposits = service.get_pending_deposits()
    
    return {
        "success": True,
        "deposits": [
            {
                "id": str(d.id),
                "user_id": str(d.user_id),
                "user_phone": d.user.phone,
                "package_name": d.package.name,
                "amount": float(d.amount),
                "reference": d.reference,
                "payment_method": d.payment_method,
                "created_at": d.created_at.isoformat(),
            }
            for d in deposits
        ],
    }


@router.put("/approve/{deposit_id}")
def approve_deposit(
    deposit_id: str,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    try:
        service = DepositService(db)
        result = service.approve_deposit(admin=admin, deposit_id=deposit_id)
        return {"success": True, "message": result["message"]}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/reject/{deposit_id}")
def reject_deposit(
    deposit_id: str,
    data: AdminDepositAction,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    try:
        service = DepositService(db)
        result = service.reject_deposit(admin=admin, deposit_id=deposit_id, reason=data.reason)
        return {"success": True, "message": result["message"]}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/history")
def get_deposit_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = DepositService(db)
    deposits = service.get_user_deposits(current_user)
    
    return {
        "success": True,
        "deposits": [
            {
                "id": str(d.id),
                "package_name": d.package.name,
                "amount": float(d.amount),
                "status": d.status,
                "reference": d.reference,
                "approved_at": d.approved_at.isoformat() if d.approved_at else None,
                "expires_at": d.expires_at.isoformat() if d.expires_at else None,
                "created_at": d.created_at.isoformat(),
            }
            for d in deposits
        ],
    }