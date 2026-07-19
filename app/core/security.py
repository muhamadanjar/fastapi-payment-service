"""
Security / auth configuration + RBAC helpers for fastapi-payment.

This service verifies JWTs signed by the auth gateway (same SECRET_KEY).
Roles are managed dynamically in the gateway, so the privileged-role set is
env-driven (ADMIN_ROLES) — never hardcode role names in endpoint code.
"""
from functools import lru_cache
from typing import Set

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SecuritySettings(BaseSettings):
    # Master switch. Set AUTH_REQUIRED=false ONLY when an upstream gateway
    # already authenticates every request before it reaches this service
    # (e.g. a BFF that strips/validates the token). When false, endpoints are
    # wide open (passthrough superuser) — use only behind a trusted proxy.
    auth_required: bool = Field(default=True, env="AUTH_REQUIRED")

    # JWT verification — shares the gateway's signing secret.
    secret_key: str = Field(default="", env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")

    # Comma-separated privileged role NAMES. Dynamic roles live in the gateway
    # DB, so this MUST stay configurable (env), never hardcoded in code.
    admin_roles: str = Field(default="admin,superuser", env="ADMIN_ROLES")

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="allow",
        env_file_encoding="utf-8",
    )


@lru_cache
def get_security_settings() -> SecuritySettings:
    return SecuritySettings()


def get_admin_roles() -> Set[str]:
    raw = get_security_settings().admin_roles or ""
    return {r.strip().lower() for r in raw.split(",") if r.strip()}


def extract_role_names(roles) -> Set[str]:
    """Normalise /auth/info `roles` (object|dict|string) -> set of lowercase names.

    The gateway returns roles as objects ({'id','name'}), not strings, so a
    naive str(role) would never match. Handle dict / object / plain string.
    """
    names: Set[str] = set()
    if not roles:
        return names
    items = roles if isinstance(roles, (list, tuple, set)) else [roles]
    for item in items:
        name = None
        if isinstance(item, str):
            name = item
        elif isinstance(item, dict):
            name = item.get("name") or item.get("slug")
        else:  # pydantic model / arbitrary object
            name = getattr(item, "name", None) or getattr(item, "slug", None)
        if name:
            names.add(str(name).strip().lower())
    return names


def user_has_admin_role(roles) -> bool:
    return bool(extract_role_names(roles).intersection(get_admin_roles()))
