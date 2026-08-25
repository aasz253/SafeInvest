import uuid
import random
import string
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.package import Package
from app.models.deposit import Deposit, DepositStatus
from app.models.admin_log import AdminLog
from app.models.earning import Earning
from app.services.referral_service import ReferralService


class DepositService:
    def __init__(self, db: Session):
        self.db = db

    def generate_reference(self) -> str:
        prefix = "SI"
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        random_suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"{prefix}-{timestamp}-{random_suffix}"

    def create_deposit(self, user: User, package_id: str, amount: float, payment_method: str = "manual") -> dict:
        package = self.db.query(Package).filter(Package.id == package_id, Package.is_active == True).first()
        if not package:
            raise ValueError("Package not found or inactive")

        if amount < float(package.amount):
            raise ValueError(f"Deposit must be at least KSH {package.amount} for {package.name}. You deposited KSH {amount}.")

        reference = self.generate_reference()

        deposit = Deposit(
            id=str(uuid.uuid4()),
            user_id=user.id,
            package_id=package_id,
            amount=amount,
            status=DepositStatus.PENDING.value,
            reference=reference,
            payment_method=payment_method,
            created_at=datetime.utcnow(),
        )

        self.db.add(deposit)
        self.db.commit()
        self.db.refresh(deposit)

        return {
            "message": "Deposit created. Waiting for admin approval.",
            "deposit": deposit,
            "package": package,
        }

    def approve_deposit(self, admin: User, deposit_id: str) -> dict:
        deposit = self.db.query(Deposit).filter(Deposit.id == deposit_id).first()
        if not deposit:
            raise ValueError("Deposit not found")

        if deposit.status != DepositStatus.PENDING.value:
            raise ValueError("Deposit already processed")

        deposit.status = DepositStatus.APPROVED.value
        deposit.approved_at = datetime.utcnow()
        deposit.expires_at = datetime.utcnow() + timedelta(days=deposit.package.duration_days if deposit.package.duration_days else 30)

        earnings_start = datetime.utcnow() + timedelta(days=1)
        daily_bonus = float(deposit.package.daily_bonus) if deposit.package.daily_bonus else 0
        duration = deposit.package.duration_days if deposit.package.duration_days else 0

        if daily_bonus > 0 and duration > 0:
            for day in range(1, duration + 1):
                earning = Earning(
                    id=str(uuid.uuid4()),
                    user_id=deposit.user_id,
                    deposit_id=deposit.id,
                    amount=daily_bonus,
                    day_number=day,
                    status="pending",
                    due_date=earnings_start + timedelta(days=day - 1),
                )
                self.db.add(earning)

        log = AdminLog(
            id=str(uuid.uuid4()),
            admin_id=admin.id,
            action="approve_deposit",
            details=str({"deposit_id": str(deposit_id), "amount": str(deposit.amount)}),
        )
        self.db.add(log)

        self.db.commit()

        user = deposit.user
        if user.invited_by_id:
            referral_service = ReferralService(self.db)
            referral_service.process_deposit_bonus(user, deposit)

        return {"message": "Deposit approved", "deposit": deposit}

    def reject_deposit(self, admin: User, deposit_id: str, reason: str = None) -> dict:
        deposit = self.db.query(Deposit).filter(Deposit.id == deposit_id).first()
        if not deposit:
            raise ValueError("Deposit not found")

        if deposit.status != DepositStatus.PENDING.value:
            raise ValueError("Deposit already processed")

        deposit.status = DepositStatus.REJECTED.value
        deposit.rejected_reason = reason

        log = AdminLog(
            id=str(uuid.uuid4()),
            admin_id=admin.id,
            action="reject_deposit",
            details=str({"deposit_id": str(deposit_id), "reason": reason}),
        )
        self.db.add(log)

        self.db.commit()

        return {"message": "Deposit rejected", "deposit": deposit}

    def get_pending_deposits(self) -> list:
        return self.db.query(Deposit).filter(Deposit.status == DepositStatus.PENDING.value).all()

    def get_user_deposits(self, user: User) -> list:
        return self.db.query(Deposit).filter(Deposit.user_id == user.id).all()