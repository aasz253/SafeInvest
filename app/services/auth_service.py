import uuid
import random
import string
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.user import User
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.sms import sms_service


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def generate_referral_code(self, phone: str) -> str:
        base = phone[-4:].upper()
        random_suffix = "".join(random.choices(string.ascii_uppercase, k=4))
        return f"SI{base}{random_suffix}"

    def register(self, phone: str, password: str, referral_code: str = None) -> dict:
        existing = self.db.query(User).filter(User.phone == phone).first()
        if existing:
            raise ValueError("Phone number already registered")

        new_referral_code = self.generate_referral_code(phone)
        inviter = None
        if referral_code:
            inviter = self.db.query(User).filter(User.referral_code == referral_code).first()

        user = User(
            id=str(uuid.uuid4()),
            phone=phone,
            password_hash=get_password_hash(password),
            referral_code=new_referral_code,
            invited_by_id=inviter.id if inviter else None,
            is_active=True,
            is_verified=False,
        )

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        otp = sms_service.generate_otp()
        user.otp_code = otp
        user.otp_expires_at = datetime.utcnow() + timedelta(minutes=10)
        self.db.commit()

        sms_service.send_otp(phone, otp)

        token = create_access_token(data={"sub": str(user.id)})

        return {
            "message": "Registration successful. Please verify your phone.",
            "token": token,
            "user": user,
            "otp_sent": True,
        }

    def verify_otp(self, phone: str, otp: str) -> dict:
        user = self.db.query(User).filter(User.phone == phone).first()
        if not user:
            raise ValueError("User not found")

        if user.otp_code != otp:
            raise ValueError("Invalid OTP")

        if user.otp_expires_at and user.otp_expires_at < datetime.utcnow():
            raise ValueError("OTP expired")

        user.is_verified = True
        user.otp_code = None
        user.otp_expires_at = None
        self.db.commit()

        token = create_access_token(data={"sub": str(user.id)})

        return {"message": "Phone verified successfully", "token": token}

    def login(self, phone: str, password: str) -> dict:
        user = self.db.query(User).filter(User.phone == phone).first()
        if not user:
            raise ValueError("Invalid credentials")

        if not verify_password(password, user.password_hash):
            raise ValueError("Invalid credentials")

        if not user.is_verified:
            otp = sms_service.generate_otp()
            user.otp_code = otp
            user.otp_expires_at = datetime.utcnow() + timedelta(minutes=10)
            self.db.commit()
            sms_service.send_otp(phone, otp)
            return {
                "message": "Phone not verified. New OTP sent.",
                "token": None,
                "requires_verification": True,
            }

        token = create_access_token(data={"sub": str(user.id)})

        return {
            "message": "Login successful",
            "token": token,
            "user": user,
        }

    def get_profile(self, user: User) -> dict:
        total_earnings = sum(float(e.amount) for e in user.earnings if e.status == "claimed")
        referral_bonus = sum(float(rb.amount) for rb in user.referral_bonuses_given if rb.status == "paid")
        active_packages = len([d for d in user.deposits if d.status == "approved"])
        total_invites = len(user.invitees)

        return {
            "id": str(user.id),
            "phone": user.phone,
            "full_name": user.full_name,
            "referral_code": user.referral_code,
            "is_verified": user.is_verified,
            "is_admin": user.is_admin,
            "created_at": user.created_at.isoformat(),
            "total_earnings": total_earnings,
            "referral_bonus": referral_bonus,
            "active_packages_count": active_packages,
            "total_invites": total_invites,
        }