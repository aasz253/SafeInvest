from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.auth import UserRegister, UserLogin, OTPVerify, Token
from app.services.auth_service import AuthService
from app.core.sms import sms_service

router = APIRouter(prefix="/auth", tags=["Auth"])


class ResendOTP(BaseModel):
    phone: str


@router.post("/register")
def register(data: UserRegister, db: Session = Depends(get_db)):
    try:
        service = AuthService(db)
        result = service.register(
            phone=data.phone,
            password=data.password,
            referral_code=data.referral_code,
        )
        return {
            "success": True,
            "message": result["message"],
            "token": result["token"],
            "otp_sent": result["otp_sent"],
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/verify-otp")
def verify_otp(data: OTPVerify, db: Session = Depends(get_db)):
    try:
        service = AuthService(db)
        result = service.verify_otp(phone=data.phone, otp=data.otp)
        return {"success": True, "message": result["message"], "token": result.get("token")}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
def login(data: UserLogin, db: Session = Depends(get_db)):
    try:
        service = AuthService(db)
        result = service.login(phone=data.phone, password=data.password)
        
        if result.get("requires_verification"):
            return {
                "success": True,
                "message": result["message"],
                "requires_verification": True,
            }
        
        return {
            "success": True,
            "message": result["message"],
            "token": result["token"],
        }
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/profile")
def get_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    service = AuthService(db)
    profile = service.get_profile(current_user)
    return {"success": True, "user": profile}


@router.post("/resend-otp")
def resend_otp(data: ResendOTP, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone == data.phone).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    otp = sms_service.generate_otp()
    user.otp_code = otp
    user.otp_expires_at = datetime.utcnow() + timedelta(minutes=10)
    db.commit()

    sms_service.send_otp(data.phone, otp)

    return {
        "success": True,
        "message": "OTP resent. Check your terminal for the code.",
        "otp": otp,
    }