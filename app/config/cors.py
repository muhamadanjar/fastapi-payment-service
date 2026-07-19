from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings


class CORSSettings(BaseSettings):
    """CORS configuration settings.

    Defaults are DEFENSIVE: no origins allowed unless explicitly set via env.
    A wildcard origin combined with allow_credentials=True is rejected by
    browsers and is unsafe, so the code default is an empty allow-list.
    Set CORS_ALLOWED_ORIGINS to your real frontend origin(s) in .env.
    """

    allowed_origins: List[str] = Field(default_factory=list, env="CORS_ALLOWED_ORIGINS")
    allowed_methods: List[str] = Field(default=["GET", "POST", "PUT", "DELETE", "OPTIONS"], env="CORS_ALLOWED_METHODS")
    allowed_headers: List[str] = Field(default=["*"], env="CORS_ALLOWED_HEADERS")
    allow_credentials: bool = Field(default=False, env="CORS_ALLOW_CREDENTIALS")
