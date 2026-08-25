from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.core.database import get_db
from app.core.deps import get_current_user, get_current_admin
from app.models.user import User
from app.models.deposit_request import DepositRequest
from app.models.admin_setting import AdminSetting

router = APIRouter(prefix="/deposit-requests", tags=["Deposit Requests"])


class DepositRequestCreate(BaseModel):
    amount: float
    mpesa_message: str


class DepositRequestAction(BaseModel):
    reason: Optional[str] = None


class PaymentNumberUpdate(BaseModel):
    payment_number: str
    payment_name: Optional[str] = None


def get_payment_number(db: Session) -> str:
    setting = db.query(AdminSetting).filter(AdminSetting.key == "payment_number").first()
    return setting.value if setting else "0712345678"


def get_payment_name(db: Session) -> str:
    setting = db.query(AdminSetting).filter(AdminSetting.key == "payment_name").first()
    return setting.value if setting else "SafeInvest"


@router.get("/payment-info")
def get_payment_info(
    db: Session = Depends(get_db),
):
    return {
        "success": True,
        "payment_number": get_payment_number(db),
        "payment_name": get_payment_name(db),
        "instructions": "Send money via M-PESA to the number above. Then paste the confirmation message below.",
    }


@router.post("/create")
def create_deposit_request(
    data: DepositRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if data.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be greater than 0")

    if len(data.mpesa_message.strip()) < 10:
        raise HTTPException(status_code=400, detail="Please paste the full M-PESA confirmation message")

    request = DepositRequest(
        id=str(__import__("uuid").uuid4()),
        user_id=current_user.id,
        amount=data.amount,
        mpesa_message=data.mpesa_message.strip(),
        status="pending",
        created_at=datetime.utcnow(),
    )
    db.add(request)
    db.commit()

    return {
        "success": True,
        "message": "Deposit request submitted. Waiting for admin approval.",
        "request": {
            "id": str(request.id),
            "amount": float(request.amount),
            "status": request.status,
            "created_at": request.created_at.isoformat(),
        },
    }


@router.get("/my-requests")
def my_deposit_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    requests = (
        db.query(DepositRequest)
        .filter(DepositRequest.user_id == current_user.id)
        .order_by(DepositRequest.created_at.desc())
        .all()
    )

    return {
        "success": True,
        "requests": [
            {
                "id": str(r.id),
                "amount": float(r.amount),
                "mpesa_message": r.mpesa_message,
                "status": r.status,
                "created_at": r.created_at.isoformat(),
                "reviewed_at": r.reviewed_at.isoformat() if r.reviewed_at else None,
            }
            for r in requests
        ],
    }


@router.get("/admin/list")
def admin_list_requests(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    requests = (
        db.query(DepositRequest)
        .order_by(DepositRequest.created_at.desc())
        .all()
    )

    return {
        "success": True,
        "requests": [
            {
                "id": str(r.id),
                "user_phone": r.user.phone,
                "amount": float(r.amount),
                "mpesa_message": r.mpesa_message,
                "status": r.status,
                "created_at": r.created_at.isoformat(),
                "reviewed_at": r.reviewed_at.isoformat() if r.reviewed_at else None,
            }
            for r in requests
        ],
    }


@router.put("/admin/approve/{request_id}")
def admin_approve_request(
    request_id: str,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    request = db.query(DepositRequest).filter(DepositRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Deposit request not found")
    if request.status != "pending":
        raise HTTPException(status_code=400, detail="Request already processed")

    request.status = "approved"
    request.reviewed_at = datetime.utcnow()
    request.reviewed_by_id = admin.id
    db.commit()

    return {
        "success": True,
        "message": f"Deposit of KSH {float(request.amount)} approved for {request.user.phone}",
    }


@router.put("/admin/reject/{request_id}")
def admin_reject_request(
    request_id: str,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    request = db.query(DepositRequest).filter(DepositRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Deposit request not found")
    if request.status != "pending":
        raise HTTPException(status_code=400, detail="Request already processed")

    request.status = "rejected"
    request.reviewed_at = datetime.utcnow()
    request.reviewed_by_id = admin.id
    db.commit()

    return {
        "success": True,
        "message": f"Deposit request rejected",
    }


@router.put("/admin/update-payment-number")
def admin_update_payment_number(
    data: PaymentNumberUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    setting = db.query(AdminSetting).filter(AdminSetting.key == "payment_number").first()
    if setting:
        setting.value = data.payment_number
    else:
        setting = AdminSetting(key="payment_number", value=data.payment_number)
        db.add(setting)

    if data.payment_name:
        name_setting = db.query(AdminSetting).filter(AdminSetting.key == "payment_name").first()
        if name_setting:
            name_setting.value = data.payment_name
        else:
            db.add(AdminSetting(key="payment_name", value=data.payment_name))

    db.commit()
    return {"success": True, "message": f"Payment number updated to {data.payment_number}"}
