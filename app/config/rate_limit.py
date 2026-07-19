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

    # Comma-separated list of TRUSTED reverse-proxy IPs. The client IP is taken
    # from X-Forwarded-For ONLY when the immediate peer (request.client.host) is
    # in this list. If empty/unset, the real peer IP is always used (no header
    # spoofing). Set this to your nginx/LB IP(s) when behind a proxy.
    trusted_proxies: str = ""
