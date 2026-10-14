"""API-key check and a small in-process rate limiter (valid for the single-instance deployment)."""

import hashlib
import hmac
import time
from collections import deque

from fastapi import Header, HTTPException, Request

from config import settings

_UNITS = {"second": 1, "minute": 60, "hour": 3600}


def parse_rate_limit(value: str) -> tuple[int, int]:
    """'30/minute' -> (30, 60)."""
    count, _, unit = value.partition("/")
    return int(count), _UNITS[unit.strip().lower()]


class RateLimiter:
    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = {}

    def check(self, identity: str, limit: str, now: float | None = None) -> int | None:
        """Record a hit; return seconds to wait if the limit is exceeded, else None."""
        count, window = parse_rate_limit(limit)
        now = time.monotonic() if now is None else now
        hits = self._hits.setdefault(identity, deque())
        while hits and now - hits[0] >= window:
            hits.popleft()
        if len(hits) >= count:
            return max(1, int(window - (now - hits[0])) + 1)
        hits.append(now)
        return None

    def reset(self) -> None:
        self._hits.clear()


limiter = RateLimiter()


async def guard(request: Request, x_api_key: str | None = Header(default=None)) -> None:
    """Dependency: authenticate with X-API-Key (when configured), then apply the rate limit."""
    expected = settings.service_api_key
    if expected and not (x_api_key and hmac.compare_digest(x_api_key, expected)):
        raise HTTPException(status_code=401, detail="Invalid or missing API key.")
    client = request.client.host if request.client else "anonymous"
    identity = hashlib.sha256((x_api_key or client).encode()).hexdigest()
    retry_after = limiter.check(identity, settings.rate_limit)
    if retry_after is not None:
        raise HTTPException(
            status_code=429, detail="Too many requests. Please slow down.", headers={"Retry-After": str(retry_after)}
        )
