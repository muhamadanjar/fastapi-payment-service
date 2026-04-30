from pydantic_settings import BaseSettings, SettingsConfigDict


class RateLimitSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="RATE_LIMIT_",
        env_file=".env",
        extra="allow"
    )

    enabled: bool = True
    strict_rpm: int = 10
    standard_rpm: int = 30
    relaxed_rpm: int = 60
