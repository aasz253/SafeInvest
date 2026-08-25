import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.deposit import Deposit, DepositStatus
from app.models.referral import ReferralBonus, BonusType, BonusStatus


class ReferralService:
    def __init__(self, db: Session):
        self.db = db

    def process_deposit_bonus(self, invitee: User, deposit: Deposit):
        if not invitee.invited_by_id:
            return

        inviter = self.db.query(User).filter(User.id == invitee.invited_by_id).first()
        if not inviter:
            return

        existing_bonus = (
            self.db.query(ReferralBonus)
            .filter(
                ReferralBonus.inviter_id == inviter.id,
                ReferralBonus.invitee_id == invitee.id,
                ReferralBonus.deposit_id == deposit.id,
            )
            .first()
        )

        if existing_bonus:
            return

        invitee_count = (
            self.db.query(ReferralBonus)
            .filter(
                ReferralBonus.inviter_id == inviter.id,
                ReferralBonus.bonus_type == BonusType.INVITER.value,
                ReferralBonus.status == BonusStatus.PAID.value,
            )
            .count()
        )

        inviter_bonus_amount = 150 + (invitee_count * 100)
        inviter_bonus = ReferralBonus(
            id=str(uuid.uuid4()),
            inviter_id=inviter.id,
            invitee_id=invitee.id,
            deposit_id=deposit.id,
            amount=inviter_bonus_amount,
            bonus_type=BonusType.INVITER.value,
            status=BonusStatus.PAID.value,
            paid_at=datetime.utcnow(),
        )
        self.db.add(inviter_bonus)

        invitee_bonus = ReferralBonus(
            id=str(uuid.uuid4()),
            inviter_id=inviter.id,
            invitee_id=invitee.id,
            deposit_id=deposit.id,
            amount=150,
            bonus_type=BonusType.INVITEE.value,
            status=BonusStatus.PAID.value,
            paid_at=datetime.utcnow(),
        )
        self.db.add(invitee_bonus)

        self.db.commit()

    def get_my_team(self, user: User) -> list:
        invitees = self.db.query(User).filter(User.invited_by_id == user.id).all()
        
        team = []
        for invitee in invitees:
            deposit = (
                self.db.query(Deposit)
                .filter(
                    Deposit.user_id == invitee.id,
                    Deposit.status == DepositStatus.APPROVED.value,
                )
                .first()
            )

            bonus = (
                self.db.query(ReferralBonus)
                .filter(
                    ReferralBonus.inviter_id == user.id,
                    ReferralBonus.invitee_id == invitee.id,
                )
                .first()
            )

            team.append({
                "id": str(invitee.id),
                "phone": invitee.phone,
                "full_name": invitee.full_name,
                "deposit_amount": float(deposit.amount) if deposit else 0,
                "bonus_amount": float(bonus.amount) if bonus else 0,
                "status": "active" if deposit else "pending",
                "created_at": invitee.created_at.isoformat(),
            })

        return team

    def get_referral_bonus(self, user: User) -> dict:
        bonuses = (
            self.db.query(ReferralBonus)
            .filter(ReferralBonus.inviter_id == user.id)
            .all()
        )

        total_bonus = sum(float(b.amount) for b in bonuses if b.status == BonusStatus.PAID.value)
        invitee_count = len(set(b.invitee_id for b in bonuses))

        return {
            "total_bonus": total_bonus,
            "invitee_count": invitee_count,
            "bonuses": [
                {
                    "id": str(b.id),
                    "amount": float(b.amount),
                    "bonus_type": b.bonus_type,
                    "status": b.status,
                    "created_at": b.created_at.isoformat(),
                }
                for b in bonuses
            ],
        }

    def get_referral_code(self, user: User) -> dict:
        return {
            "referral_code": user.referral_code,
            "referral_link": f"https://safeinvest.co.ke/register?ref={user.referral_code}",
        }