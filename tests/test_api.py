import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import Base, get_db
from app.core.security import get_password_hash
from app.models.user import User
from app.models.package import Package
import uuid
import random
import string

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def test_user():
    db = TestingSessionLocal()
    try:
        phone = f"0712{random.randint(100000, 999999)}"
        user = User(
            id=uuid.uuid4(),
            phone=phone,
            password_hash=get_password_hash("TestPass123"),
            referral_code=f"SI{phone[-4:]}{''.join(random.choices(string.ascii_uppercase, k=4))}",
            is_active=True,
            is_verified=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()


@pytest.fixture
def test_admin():
    db = TestingSessionLocal()
    try:
        admin = User(
            id=uuid.uuid4(),
            phone="0711111111",
            password_hash=get_password_hash("AdminPass123"),
            referral_code="SIADM1111",
            is_active=True,
            is_admin=True,
            is_verified=True,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        return admin
    finally:
        db.close()


@pytest.fixture
def test_package():
    db = TestingSessionLocal()
    try:
        package = Package(
            id=uuid.uuid4(),
            name="Bronze",
            amount=450,
            daily_bonus=80,
            duration_days=10,
            total_return=800,
            is_increasing=False,
            is_active=True,
        )
        db.add(package)
        db.commit()
        db.refresh(package)
        return package
    finally:
        db.close()


class TestAuth:
    def test_register(self, client):
        response = client.post(
            "/api/v1/auth/register",
            json={"phone": "0722123456", "password": "TestPass123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "token" in data

    def test_login(self, client, test_user):
        response = client.post(
            "/api/v1/auth/login",
            json={"phone": test_user.phone, "password": "TestPass123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "token" in data

    def test_invalid_login(self, client):
        response = client.post(
            "/api/v1/auth/login",
            json={"phone": "0722999999", "password": "WrongPass"},
        )
        assert response.status_code == 401


class TestPackages:
    def test_list_packages(self, client, test_package):
        response = client.get("/api/v1/packages/list")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert len(data["packages"]) > 0

    def test_get_package_details(self, client, test_package):
        response = client.get(f"/api/v1/packages/details/{test_package.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["package"]["name"] == "Bronze"