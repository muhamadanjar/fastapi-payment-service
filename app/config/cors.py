from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings


class CORSSettings(BaseSettings):
    """CORS configuration settings."""
    
    allowed_origins: List[str] = Field(default=["*"], env="CORS_ALLOWED_ORIGINS")
    allowed_methods: List[str] = Field(default=["*"], env="CORS_ALLOWED_METHODS")
    allowed_headers: List[str] = Field(default=["*"], env="CORS_ALLOWED_HEADERS")
    allow_credentials: bool = Field(default=True, env="CORS_ALLOW_CREDENTIALS")
