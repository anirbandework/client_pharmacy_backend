from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    database_url: str = "sqlite:///./pharmacy.db"
    redis_url: str = "redis://localhost:6379"
    whatsapp_api_url: str = ""
    whatsapp_token: str = ""
    whatsapp_from_number: str = "+14155238886"
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    reminder_days_before: int = 5
    cash_difference_limit: float = 100.0
    cash_difference_threshold: float = 50.0
    gemini_api_key: str = ""
    
    class Config:
        env_file = ".env"

settings = Settings()