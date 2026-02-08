from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./pharmacy.db")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    whatsapp_api_url: str = os.getenv("WHATSAPP_API_URL", "")
    whatsapp_token: str = os.getenv("WHATSAPP_TOKEN", "")
    whatsapp_from_number: str = os.getenv("WHATSAPP_FROM_NUMBER", "+14155238886")
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    reminder_days_before: int = int(os.getenv("REMINDER_DAYS_BEFORE", "5"))
    cash_difference_limit: float = float(os.getenv("CASH_DIFFERENCE_LIMIT", "100.0"))
    cash_difference_threshold: float = float(os.getenv("CASH_DIFFERENCE_THRESHOLD", "50.0"))
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    
    class Config:
        env_file = ".env"

settings = Settings()