from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.core.security import get_password_hash
from app.models.user import User
from app.models.package import Package
from app.models.admin_setting import AdminSetting
from app.models.base import Base
import uuid
import random
import string


def generate_referral_code(phone: str) -> str:
    base = phone[-4:].upper()
    random_suffix = "".join(random.choices(string.ascii_uppercase, k=4))
    return f"SI{base}{random_suffix}"


def seed_packages(db: Session):
    packages = [
        {"name": "Bronze", "amount": 450, "daily_bonus": 80, "duration_days": 10, "total_return": 800, "is_increasing": False, "description": "Perfect starter plan. Invest 450 KSH, earn 80 KSH daily for 10 days."},
        {"name": "Silver", "amount": 950, "daily_bonus": 125, "duration_days": 16, "total_return": 2000, "is_increasing": False, "description": "Popular choice. Invest 950 KSH, earn 125 KSH daily for 16 days."},
        {"name": "Gold", "amount": 1500, "daily_bonus": 150, "duration_days": 20, "total_return": 3000, "is_increasing": False, "description": "Premium plan. Invest 1,500 KSH, earn 150 KSH daily for 20 days."},
        {"name": "Platinum", "amount": 2850, "daily_bonus": 225, "duration_days": 20, "total_return": 4500, "is_increasing": False, "description": "High-value plan. Invest 2,850 KSH, earn 225 KSH daily for 20 days."},
        {"name": "Diamond", "amount": 4700, "daily_bonus": 335, "duration_days": 30, "total_return": 10050, "is_increasing": False, "description": "Top-tier plan. Invest 4,700 KSH, earn 335 KSH daily for 30 days."},
        {"name": "VIP 1", "amount": 9900, "daily_bonus": None, "duration_days": None, "total_return": None, "is_increasing": True, "description": "VIP tier. Progressive daily returns that increase over time."},
        {"name": "VIP 2", "amount": 18000, "daily_bonus": None, "duration_days": None, "total_return": None, "is_increasing": True, "description": "Premium VIP tier. Higher progressive returns."},
        {"name": "VIP 3", "amount": 45000, "daily_bonus": None, "duration_days": None, "total_return": None, "is_increasing": True, "description": "Elite VIP tier. Maximum progressive returns."},
        {"name": "VIP 4", "amount": 99000, "daily_bonus": None, "duration_days": None, "total_return": None, "is_increasing": True, "description": "Ultimate VIP tier. The highest returns in SafeInvest."},
    ]
    
    existing = db.query(Package).count()
    if existing > 0:
        print(f"  {existing} packages already exist. Skipping...")
        return
    
    for p in packages:
        package = Package(
            id=str(uuid.uuid4()),
            name=p["name"],
            amount=p["amount"],
            daily_bonus=p["daily_bonus"],
            duration_days=p["duration_days"],
            total_return=p["total_return"],
            is_increasing=p["is_increasing"],
            is_active=True,
            description=p["description"],
        )
        db.add(package)
    
    db.commit()
    print(f"  Seeded {len(packages)} packages")


def seed_admin(db: Session):
    admin_phone = "0712345678"
    admin = db.query(User).filter(User.phone == admin_phone).first()
    
    if admin:
        print(f"  Admin already exists ({admin_phone}). Skipping...")
        return
    
    admin = User(
        id=str(uuid.uuid4()),
        phone=admin_phone,
        password_hash=get_password_hash("Admin@123"),
        referral_code=generate_referral_code(admin_phone),
        full_name="SafeInvest Admin",
        is_active=True,
        is_admin=True,
        is_verified=True,
    )
    
    db.add(admin)
    db.commit()
    print(f"  Admin created: {admin_phone} / Admin@123")


def seed_payment_settings(db: Session):
    existing = db.query(AdminSetting).filter(AdminSetting.key == "payment_number").first()
    if existing:
        print(f"  Payment number already set ({existing.value}). Skipping...")
        return

    setting = AdminSetting(
        id=str(uuid.uuid4()),
        key="payment_number",
        value="0712345678",
    )
    db.add(setting)

    setting2 = AdminSetting(
        id=str(uuid.uuid4()),
        key="payment_name",
        value="SafeInvest M-PESA",
    )
    db.add(setting2)
    db.commit()
    print("  Payment settings seeded: 0712345678")


def run_seed():
    print("Seeding SafeInvest database...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        seed_packages(db)
        seed_admin(db)
        seed_payment_settings(db)
        print("Seeding complete!")
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()