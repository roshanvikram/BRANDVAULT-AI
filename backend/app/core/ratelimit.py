"""Small in-process rate limiter (Phase 1a).

Sliding-window counter per (bucket, client IP). Protects sign-in from password
guessing and the LLM-backed routes from runaway cost. In-memory, so limits are
per backend process; a multi-instance deployment would move this to Redis.
"""
from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status

from backend.app.core.config import settings


class _Limiter:
    def __init__(self) -> None:
        self._hits: dict[tuple[str, str], deque] = defaultdict(deque)
        self._lock = threading.Lock()

    def hit(self, bucket: str, key: str, limit: int, window: float) -> float | None:
        """Record a hit. Returns seconds to wait if over the limit, else None."""
        now = time.monotonic()
        with self._lock:
            q = self._hits[(bucket, key)]
            while q and now - q[0] > window:
                q.popleft()
            if len(q) >= limit:
                return max(1.0, window - (now - q[0]))
            q.append(now)
            return None

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


limiter = _Limiter()


def rate_limit(bucket: str, per_minute: int):
    """Dependency factory: allow `per_minute` requests per client IP."""
    def _dep(request: Request) -> None:
        if not settings.RATE_LIMIT_ENABLED:
            return
        client = request.client.host if request.client else "unknown"
        wait = limiter.hit(bucket, client, per_minute, 60.0)
        if wait is not None:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many requests. Try again in {int(wait)} seconds.",
                headers={"Retry-After": str(int(wait))},
            )
    return _dep
