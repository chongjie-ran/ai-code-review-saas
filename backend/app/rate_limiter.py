"""
CodeLens AI - Rate Limiting Module
Token bucket rate limiting for API endpoints.
"""
import os
import time
from collections import defaultdict
from typing import Optional, Literal
from dataclasses import dataclass
from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware


# ─── Configuration ──────────────────────────────────────────────

DEFAULT_LIMIT = int(os.getenv("CODELENS_RATE_LIMIT", "100"))      # requests per window
DEFAULT_WINDOW = int(os.getenv("CODELENS_RATE_WINDOW", "60"))   # window in seconds
ANONYMOUS_LIMIT = int(os.getenv("CODELENS_ANONYMOUS_LIMIT", "20"))


@dataclass
class RateLimitConfig:
    """Rate limit configuration for an endpoint or user tier"""
    limit: int
    window_seconds: int

    @property
    def window_ms(self) -> int:
        return self.window_seconds * 1000


# Tier-based limits
RATE_LIMITS = {
    "anonymous": RateLimitConfig(limit=ANONYMOUS_LIMIT, window_seconds=60),
    "free": RateLimitConfig(limit=100, window_seconds=60),
    "pro": RateLimitConfig(limit=1000, window_seconds=60),
    "enterprise": RateLimitConfig(limit=10000, window_seconds=60),
    "api": RateLimitConfig(limit=100, window_seconds=60),  # /api/v1/analyze
}


# ─── Token Bucket Store ─────────────────────────────────────────

class TokenBucketStore:
    """
    In-memory token bucket rate limiter.
    Uses per-key state: {tokens, last_refill}
    """

    def __init__(self):
        self._buckets: dict[str, dict] = defaultdict(lambda: {"tokens": 0.0, "last_refill": 0.0})

    def _refill(self, key: str, config: RateLimitConfig):
        """Refill tokens based on elapsed time"""
        bucket = self._buckets[key]
        now = time.monotonic()
        elapsed = now - bucket["last_refill"]

        if elapsed > 0:
            # Add tokens proportional to elapsed time
            tokens_to_add = (elapsed / config.window_seconds) * config.limit
            bucket["tokens"] = min(config.limit, bucket["tokens"] + tokens_to_add)
            bucket["last_refill"] = now

    def check(self, key: str, config: RateLimitConfig, cost: int = 1) -> tuple[bool, dict]:
        """
        Check if request is allowed.
        Returns (allowed, info_dict).
        """
        self._refill(key, config)
        bucket = self._buckets[key]

        if bucket["tokens"] >= cost:
            bucket["tokens"] -= cost
            allowed = True
        else:
            allowed = False

        remaining = max(0, int(bucket["tokens"]))
        retry_after = 0 if allowed else int(config.window_seconds * (1 - bucket["tokens"] / config.limit)) + 1

        return allowed, {
            "limit": config.limit,
            "remaining": remaining,
            "reset_seconds": retry_after,
            "tier": key.split(":")[0] if ":" in key else "default",
        }

    def clear(self):
        """Clear all buckets"""
        self._buckets.clear()


# Global store
_rate_limit_store = TokenBucketStore()


# ─── Rate Limit Dependency ─────────────────────────────────────

def get_rate_limit_key(
    request: Request,
    user_tier: str = "anonymous",
) -> str:
    """
    Generate rate limit key for a request.
    Uses IP for anonymous, user_id for authenticated.
    """
    # Try to get authenticated user
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        # Use token prefix as key (partial, doesn't decode full JWT)
        return f"{user_tier}:{auth_header[7:20]}"

    # Fall back to IP
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        ip = forwarded.split(",")[0].strip()
    else:
        ip = request.client.host if request.client else "unknown"

    return f"{user_tier}:{ip}"


def rate_limit(
    request: Request,
    tier: str = "anonymous",
    cost: int = 1,
) -> dict:
    """
    Rate limit check as a dependency-like function.
    Raises HTTPException 429 if limit exceeded.

    Usage:
        info = rate_limit(request, tier="free")
        # or in FastAPI route:
        user_tier = "free"  # determine from user
        info = rate_limit(request, tier=user_tier)
    """
    config = RATE_LIMITS.get(tier, RATE_LIMITS["anonymous"])
    key = get_rate_limit_key(request, tier)
    allowed, info = _rate_limit_store.check(key, config, cost)

    if not allowed:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "retry_after_seconds": info["reset_seconds"],
                "limit": info["limit"],
                "remaining": 0,
            },
            headers={
                "X-RateLimit-Limit": str(info["limit"]),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(info["reset_seconds"]),
                "Retry-After": str(info["reset_seconds"]),
            },
        )

    return info


# ─── Middleware ──────────────────────────────────────────────────

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Automatic rate limiting middleware.
    Applies to /api/* endpoints.
    """

    EXCLUDED_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Skip excluded paths and non-API paths
        if path in self.EXCLUDED_PATHS or not path.startswith("/api/"):
            return await call_next(request)

        # Determine tier from token
        tier = "anonymous"
        auth = request.headers.get("authorization", "")
        if auth.startswith("Bearer "):
            try:
                from .auth import decode_token
                payload = decode_token(auth[7:])
                user_id = int(payload.get("sub", 0))
                tier = self._get_user_tier(user_id)
            except Exception:
                tier = "anonymous"

        config = RATE_LIMITS.get(tier, RATE_LIMITS["anonymous"])
        key = get_rate_limit_key(request, tier)
        allowed, info = _rate_limit_store.check(key, config)

        # Always process request, but add headers
        response = await call_next(request)

        response.headers["X-RateLimit-Limit"] = str(info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(info["reset_seconds"])

        if not allowed:
            response.status_code = 429
            response.headers["Retry-After"] = str(info["reset_seconds"])

        return response

    def _get_user_tier(self, user_id: int) -> str:
        """Determine user tier from database"""
        try:
            from .auth import get_db
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT plan FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            conn.close()
            return row["plan"] if row else "anonymous"
        except Exception:
            return "anonymous"


# ─── Per-Endpoint Limit Overrides ────────────────────────────────

ENDPOINT_LIMITS = {
    "/api/v1/analyze": "api",
    "/api/v1/review-pr": "api",
}
