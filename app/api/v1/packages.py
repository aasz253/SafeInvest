from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.package import Package

router = APIRouter(prefix="/packages", tags=["Packages"])


@router.get("/list")
def list_packages(db: Session = Depends(get_db)):
    packages = db.query(Package).filter(Package.is_active == True).all()
    
    return {
        "success": True,
        "packages": [
            {
                "id": str(p.id),
                "name": p.name,
                "amount": float(p.amount),
                "daily_bonus": float(p.daily_bonus) if p.daily_bonus else None,
                "duration_days": p.duration_days,
                "total_return": float(p.total_return) if p.total_return else None,
                "is_increasing": p.is_increasing,
                "description": p.description,
            }
            for p in packages
        ],
    }


@router.get("/details/{package_id}")
def get_package(package_id: str, db: Session = Depends(get_db)):
    package = db.query(Package).filter(Package.id == package_id, Package.is_active == True).first()
    
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")
    
    return {
        "success": True,
        "package": {
            "id": str(package.id),
            "name": package.name,
            "amount": float(package.amount),
            "daily_bonus": float(package.daily_bonus) if package.daily_bonus else None,
            "duration_days": package.duration_days,
            "total_return": float(package.total_return) if package.total_return else None,
            "is_increasing": package.is_increasing,
            "description": package.description,
        },
    }