"""Rate limiting shared by every server instance.

Counters live in the database (table ``rate_limit_counters``), so two or more
backend processes or containers enforce one limit together. It uses the
sliding-window counter method: the current minute's count plus the previous
minute's count weighted by how much of it still overlaps the last 60 seconds.

Protects sign-in from password guessing and the LLM-backed routes from runaway
cost. If the database cannot be reached, it falls back to an in-memory limiter
for that process, so a limiter problem never blocks real requests.
Set RATE_LIMIT_BACKEND=memory to use only the in-memory limiter.
"""
from __future__ import annotations

import os
import random
import threading
import time
from collections import defaultdict, deque
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import delete, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.db.session import get_db
from backend.app.models.ratelimit import RateLimitCounter


class _MemoryLimiter:
    def __init__(self) -> None:
        self._hits: dict[tuple[str, str], deque] = defaultdict(deque)
        self._lock = threading.Lock()

    def hit(self, bucket: str, key: str, limit: int, window: float) -> Optional[float]:
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


class _SharedLimiter:
    """Database-backed limiter with an in-memory fallback."""

    def __init__(self) -> None:
        self.memory = _MemoryLimiter()
        self._generation = 0  # bumped by reset() so earlier counters are ignored

    def _key(self, key: str) -> str:
        return f"{self._generation}:{key}"[:120]

    def hit(self, bucket: str, key: str, limit: int, window: float = 60.0,
            db: Optional[Session] = None) -> Optional[float]:
        """Record a hit. Returns seconds to wait if over the limit, else None."""
        if db is None or os.getenv("RATE_LIMIT_BACKEND", "database").lower() == "memory":
            return self.memory.hit(bucket, key, limit, window)
        try:
            return self._db_hit(db, bucket[:40], self._key(key), limit)
        except SQLAlchemyError:
            db.rollback()
            return self.memory.hit(bucket, key, limit, window)

    def _db_hit(self, db: Session, bucket: str, client: str, limit: int) -> Optional[float]:
        now = time.time()
        minute = int(now // 60)
        elapsed = now - minute * 60
        rows = {r.window: r.count for r in db.query(RateLimitCounter).filter(
            RateLimitCounter.bucket == bucket, RateLimitCounter.client == client,
            RateLimitCounter.window.in_([minute - 1, minute]))}
        estimate = rows.get(minute - 1, 0) * (1 - elapsed / 60) + rows.get(minute, 0)
        if estimate >= limit:
            db.commit()
            return max(1.0, 60 - elapsed)
        changed = db.execute(update(RateLimitCounter).where(
            RateLimitCounter.bucket == bucket, RateLimitCounter.client == client,
            RateLimitCounter.window == minute).values(count=RateLimitCounter.count + 1)).rowcount
        if not changed:
            try:
                db.add(RateLimitCounter(bucket=bucket, client=client, window=minute, count=1))
                db.flush()
            except IntegrityError:  # another instance inserted it first
                db.rollback()
                db.execute(update(RateLimitCounter).where(
                    RateLimitCounter.bucket == bucket, RateLimitCounter.client == client,
                    RateLimitCounter.window == minute).values(count=RateLimitCounter.count + 1))
        if random.random() < 0.02:  # occasionally drop counters older than 5 minutes
            db.execute(delete(RateLimitCounter).where(RateLimitCounter.window < minute - 5))
        db.commit()
        return None

    def reset(self) -> None:
        self._generation += 1
        self.memory.reset()


limiter = _SharedLimiter()


def rate_limit(bucket: str, per_minute: int):
    """Dependency factory: allow `per_minute` requests per client IP, across all instances."""
    def _dep(request: Request, db: Session = Depends(get_db)) -> None:
        if not settings.RATE_LIMIT_ENABLED:
            return
        client = request.client.host if request.client else "unknown"
        wait = limiter.hit(bucket, client, per_minute, 60.0, db=db)
        if wait is not None:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many requests. Try again in {int(wait)} seconds.",
                headers={"Retry-After": str(int(wait))},
            )
    return _dep
