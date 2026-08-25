from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.services.referral_service import ReferralService

router = APIRouter(prefix="/referrals", tags=["Referrals"])


@router.get("/my-team")
def get_my_team(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ReferralService(db)
    team = service.get_my_team(current_user)
    
    return {
        "success": True,
        "total_invites": len(team),
        "team": team,
    }


@router.get("/bonus")
def get_referral_bonus(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ReferralService(db)
    result = service.get_referral_bonus(current_user)
    return {"success": True, **result}


@router.get("/code")
def get_referral_code(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ReferralService(db)
    result = service.get_referral_code(current_user)
    return {"success": True, **result}