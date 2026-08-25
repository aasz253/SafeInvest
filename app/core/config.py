from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    APP_NAME: str = "SafeInvest"
    DEBUG: bool = True
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    DATABASE_URL: str = "sqlite:///./safeinvest.db"

    AFRICASTALKING_USERNAME: str = "sandbox"
    AFRICASTALKING_API_KEY: str = ""
    AFRICASTALKING_SENDER_ID: str = "SafeInvest"

    FRONTEND_URL: str = "http://localhost:3000"

    ADMIN_PHONE: str = "0712345678"
    ADMIN_EMAIL: str = "admin@safeinvest.co.ke"

    TIMEZONE: str = "Africa/Nairobi"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
