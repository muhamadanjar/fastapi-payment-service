"""
Authentication + authorization dependencies for FastAPI routes.

Usage:
    from app.core.auth import get_current_user, require_roles

    # Protect a whole router (composes with parent router deps):
    router = APIRouter(dependencies=[Depends(get_current_user)])

    # Admin-only router (dynamic ADMIN_ROLES from env):
    admin_router = APIRouter(dependencies=[Depends(require_roles())])

    # Per-endpoint override:
    @router.post("/x")
    async def create(current_user=Depends(require_roles())):
        ...
"""
from typing import Any, Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import get_security_settings, user_has_admin_role, extract_role_names

# auto_error=False so we can return a clean 401 when AUTH_REQUIRED but no token.
security = HTTPBearer(auto_error=False)


class RemoteUserInfo:
    """Lightweight representation of the authenticated principal from the JWT."""

    def __init__(self, **data: Any):
        self.id: Optional[str] = data.get("id") or data.get("sub")
        self.email: Optional[str] = data.get("email")
        self.name: Optional[str] = data.get("name") or data.get("preferred_username")
        self.is_active: bool = bool(data.get("is_active", True))
        self.is_superuser: bool = bool(data.get("is_superuser", False))
        self.roles = data.get("roles") or []
        self.privileges = data.get("privileges") or []
        self.claims = data  # raw JWT claims, for debugging


def _decode_token(token: str) -> dict:
    settings = get_security_settings()
    if not settings.secret_key:
        # Misconfiguration: cannot verify signature. Refuse rather than trust.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Auth not configured (missing SECRET_KEY)",
        )
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> RemoteUserInfo:
    settings = get_security_settings()

    # Escape hatch: an upstream gateway already authenticated the request.
    if not settings.auth_required:
        return RemoteUserInfo(id="gateway-passthrough", is_superuser=True, is_active=True, roles=[])

    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    claims = _decode_token(credentials.credentials)
    user = RemoteUserInfo(**claims)

    # Inactive-user enforcement — covers every endpoint depending on this.
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return user


def require_roles(*required_roles: str):
    """Dependency factory.

    require_roles()            -> enforces ADMIN_ROLES from env (dynamic mode)
    require_roles("a","b")     -> enforces one of the given roles (static mode)
    Superusers always pass.
    """

    async def _checker(
        current_user: RemoteUserInfo = Depends(get_current_user),
    ) -> RemoteUserInfo:
        if current_user.is_superuser:
            return current_user
        if not required_roles:
            # DYNAMIC MODE: enforce ADMIN_ROLES from env
            if user_has_admin_role(current_user.roles):
                return current_user
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Requires an administrative role",
            )
        user_roles = extract_role_names(current_user.roles)
        if not user_roles.intersection({r.lower() for r in required_roles}):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {', '.join(required_roles)}",
            )
        return current_user

    return _checker


# Semantic alias — identical behaviour; use whichever reads clearer.
get_current_active_user = get_current_user
