import asyncio
import time
from collections import defaultdict, deque
from typing import Optional

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config.rate_limit import RateLimitSettings


class SlidingWindowCounter:
    def __init__(self):
        self._windows: dict[str, deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def is_allowed(self, key: str, limit: int, window_secs: int = 60) -> tuple[bool, int]:
        async with self._lock:
            now = time.monotonic()
            cutoff = now - window_secs
            q = self._windows[key]

            while q and q[0] < cutoff:
                q.popleft()

            if len(q) >= limit:
                retry_after = max(1, int(window_secs - (now - q[0])))
                return False, retry_after

            q.append(now)
            return True, 0


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, settings: Optional[RateLimitSettings] = None):
        super().__init__(app)
        self.settings = settings or RateLimitSettings()
        self.counter = SlidingWindowCounter()

    def _get_client_ip(self, request: Request) -> str:
        peer = request.client.host if request.client else "unknown"
        # Only trust X-Forwarded-For when the immediate peer is a configured proxy.
        trusted = {t.strip() for t in (self.settings.trusted_proxies or "").split(",") if t.strip()}
        if trusted and peer in trusted:
            if x_forwarded_for := request.headers.get("x-forwarded-for"):
                return x_forwarded_for.split(",")[0].strip()
        return peer

    def _get_tier(self, path: str, method: str) -> str:
        if path.startswith("/webhook/payment/"):
            return "strict"

        if path == "/api/vouchers/validate":
            return "strict"

        if path.startswith("/api/transactions/") and method in ("POST",):
            if "/pay" in path or "/cancel" in path or "/refund" in path:
                return "standard"

        if path == "/api/transactions" and method == "POST":
            return "standard"

        if path.startswith("/api/health"):
            return "skip"

        return "relaxed"

    async def dispatch(self, request: Request, call_next):
        if not self.settings.enabled:
            return await call_next(request)

        tier = self._get_tier(request.url.path, request.method)
        if tier == "skip":
            return await call_next(request)

        client_ip = self._get_client_ip(request)
        key = f"{client_ip}:{tier}"

        limit_map = {
            "strict": self.settings.strict_rpm,
            "standard": self.settings.standard_rpm,
            "relaxed": self.settings.relaxed_rpm,
        }
        limit = limit_map.get(tier, self.settings.relaxed_rpm)

        is_allowed, retry_after = await self.counter.is_allowed(key, limit, window_secs=60)

        if not is_allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "message": f"Too many requests. Try again in {retry_after} seconds.",
                    "details": {
                        "retry_after": retry_after,
                        "limit": limit,
                        "window": 60,
                    }
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                }
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        return response
