from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.user import User
from app.models.deposit import Deposit, DepositStatus
from app.models.earning import Earning, EarningStatus
from app.models.package import Package


class EarningService:
    def __init__(self, db: Session):
        self.db = db

    def get_today_earning(self, user: User) -> dict:
        today = datetime.utcnow().date()

        approved_deposits = (
            self.db.query(Deposit)
            .filter(
                Deposit.user_id == user.id,
                Deposit.status == DepositStatus.APPROVED.value,
                Deposit.expires_at > datetime.utcnow(),
            )
            .all()
        )

        today_earning = 0
        earning_claimed = False
        packages_info = []

        for deposit in approved_deposits:
            package = deposit.package
            if not package.daily_bonus:
                continue

            day_earning = (
                self.db.query(Earning)
                .filter(
                    Earning.deposit_id == deposit.id,
                    func.date(Earning.due_date) == today,
                )
                .first()
            )

            if day_earning:
                if day_earning.status == EarningStatus.CLAIMED.value:
                    earning_claimed = True
                today_earning += float(day_earning.amount)

            days_completed = (
                self.db.query(Earning)
                .filter(
                    Earning.deposit_id == deposit.id,
                    Earning.status == EarningStatus.CLAIMED.value,
                )
                .count()
            )

            total_days = package.duration_days if package.duration_days else 0
            earned_so_far = (
                self.db.query(func.sum(Earning.amount))
                .filter(
                    Earning.deposit_id == deposit.id,
                    Earning.status == EarningStatus.CLAIMED.value,
                )
                .scalar()
                or 0
            )

            next_earning = (
                self.db.query(Earning)
                .filter(
                    Earning.deposit_id == deposit.id,
                    Earning.status == EarningStatus.PENDING.value,
                )
                .order_by(Earning.due_date.asc())
                .first()
            )

            packages_info.append({
                "deposit_id": str(deposit.id),
                "package_name": package.name,
                "invested": float(deposit.amount),
                "days_completed": days_completed,
                "days_total": total_days,
                "earned_so_far": float(earned_so_far),
                "next_earning_due": next_earning.due_date.isoformat() if next_earning else None,
            })

        return {
            "today_earning": float(today_earning),
            "earning_claimed": earning_claimed,
            "active_packages": packages_info,
        }

    def claim_daily(self, user: User, deposit_id: str) -> dict:
        deposit = (
            self.db.query(Deposit)
            .filter(
                Deposit.id == deposit_id,
                Deposit.user_id == user.id,
                Deposit.status == DepositStatus.APPROVED.value,
            )
            .first()
        )

        if not deposit:
            raise ValueError("Deposit not found or not approved")

        today = datetime.utcnow().date()

        earning = (
            self.db.query(Earning)
            .filter(
                Earning.deposit_id == deposit.id,
                Earning.status == EarningStatus.PENDING.value,
                func.date(Earning.due_date) <= today,
            )
            .order_by(Earning.due_date.desc())
            .first()
        )

        if not earning:
            raise ValueError("No pending earnings to claim")

        earning.status = EarningStatus.CLAIMED.value
        earning.claimed_at = datetime.utcnow()

        self.db.commit()

        return {
            "message": f"Day {earning.day_number} earning claimed",
            "amount": float(earning.amount),
            "day_number": earning.day_number,
        }

    def get_earning_history(self, user: User) -> list:
        return (
            self.db.query(Earning)
            .filter(Earning.user_id == user.id)
            .order_by(Earning.due_date.desc())
            .all()
        )

    def get_earning_summary(self, user: User) -> dict:
        total_earned = (
            self.db.query(func.sum(Earning.amount))
            .filter(
                Earning.user_id == user.id,
                Earning.status == EarningStatus.CLAIMED.value,
            )
            .scalar()
            or 0
        )

        pending_amount = (
            self.db.query(func.sum(Earning.amount))
            .filter(
                Earning.user_id == user.id,
                Earning.status == EarningStatus.PENDING.value,
            )
            .scalar()
            or 0
        )

        today = datetime.utcnow().date()

        today_earning = (
            self.db.query(func.sum(Earning.amount))
            .filter(
                Earning.user_id == user.id,
                func.date(Earning.due_date) == today,
            )
            .scalar()
            or 0
        )

        return {
            "total_earned": float(total_earned),
            "pending_amount": float(pending_amount),
            "today_earning": float(today_earning),
        }