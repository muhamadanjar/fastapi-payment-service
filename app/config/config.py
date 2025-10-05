from functools import lru_cache
from typing import Optional
from pydantic import EmailStr, Field
from pydantic_settings import BaseSettings
from .database import DatabaseSettings

class Settings(BaseSettings):
    # Project
    PROJECT_NAME: str = Field(default="FastAPI Payment")
    VERSION: str = Field(default="1.0.0")
    DESCRIPTION: str = "FastAPI payment"

    DATABASE: Optional[DatabaseSettings] = Field(default=None, efault_factory=DatabaseSettings)



@lru_cache
def get_settings() -> Settings:
    return Settings()