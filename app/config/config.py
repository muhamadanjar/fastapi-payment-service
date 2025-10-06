from functools import lru_cache
from typing import Optional
from pydantic import EmailStr, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.config.cors import CORSSettings
from .database import DatabaseSettings
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent.parent

print("BASE DIR", BASE_DIR)

class Settings(BaseSettings):
    # Project
    PROJECT_NAME: str = Field(default="FastAPI Payment")
    VERSION: str = Field(default="1.0.0")
    DESCRIPTION: str = "FastAPI payment"

    DATABASE: DatabaseSettings = Field(default_factory=DatabaseSettings)
    CORS:Optional[CORSSettings] = Field(default=None,)

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"), 
        extra="allow", 
        env_file_encoding="utf-8"
    )

settings = Settings()

@lru_cache
def get_settings() -> Settings:
    return Settings()