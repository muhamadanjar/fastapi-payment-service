from functools import lru_cache
from typing import Optional
from pydantic import EmailStr, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.config.cors import CORSSettings
from app.config.rate_limit import RateLimitSettings
from .database import DatabaseSettings
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    # Project
    PROJECT_NAME: str = Field(default="FastAPI Payment")
    VERSION: str = Field(default="1.0.0")
    DESCRIPTION: str = "FastAPI payment"

    DATABASE: DatabaseSettings = Field(default_factory=DatabaseSettings)
    CORS: Optional[CORSSettings] = Field(default=None)
    RATE_LIMIT: Optional[RateLimitSettings] = Field(default_factory=RateLimitSettings)

    LOG_LEVEL: str = Field(default="INFO")
    LOG_FILE: str = Field(default="payment.log")
    LOG_FORMAT: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    LOG_DATE_FORMAT: str = Field(default="%Y-%m-%d %H:%M:%S")
    LOG_MAX_BYTES: int = Field(default=10485760)
    LOG_BACKUP_COUNT: int = Field(default=5)
    LOG_ENCODING: str = Field(default="utf-8")
    LOG_ENABLE_JSON: bool = Field(default=False)
    LOG_ENABLE_CONSOLE: bool = Field(default=True)

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"), 
        extra="allow", 
        env_file_encoding="utf-8"
    )

settings = Settings()

@lru_cache
def get_settings() -> Settings:
    return Settings()