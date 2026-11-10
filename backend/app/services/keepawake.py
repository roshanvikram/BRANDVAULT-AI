"""Keep the free-hosted services awake during the day.

Render's free plan stops a service after 15 minutes without requests, and gives
750 free hours a month shared by all services. While this server is up, it calls
its own public health URL and the frontend every 10 minutes, but only inside a
daily window (default 09:00–20:30 IST), so two services stay within the free hours.

Zero configuration on Render: it uses RENDER_EXTERNAL_URL (set by Render) and the
https origins in BACKEND_CORS_ORIGINS. Turn it off with KEEP_AWAKE=off, change the
window with KEEP_AWAKE_WINDOW="09:00-20:30" (IST), or list URLs in KEEP_AWAKE_URLS.
A sleeping server cannot wake itself: the first visit, or the GitHub Actions job,
wakes it, and from then on it stays awake until the window ends.
"""
from __future__ import annotations

import asyncio
import datetime
import logging
import os
import urllib.request
from typing import Dict, List, Optional, Tuple

log = logging.getLogger("brandvault.keepawake")

IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
INTERVAL_SECONDS = 600

state: Dict = {"enabled": False, "targets": [], "window": None, "last_ping": None, "last_results": {}}


def _window() -> Tuple[datetime.time, datetime.time]:
    raw = os.getenv("KEEP_AWAKE_WINDOW", "09:00-20:30")
    try:
        a, b = raw.split("-")
        start = datetime.time(*map(int, a.strip().split(":")))
        end = datetime.time(*map(int, b.strip().split(":")))
        return start, end
    except ValueError:
        return datetime.time(9, 0), datetime.time(20, 30)


def in_window(now: Optional[datetime.datetime] = None) -> bool:
    now = (now or datetime.datetime.now(IST)).astimezone(IST)
    start, end = _window()
    t = now.time()
    return start <= t <= end if start <= end else (t >= start or t <= end)


def targets(cors_origins: List[str]) -> List[str]:
    explicit = [u.strip() for u in os.getenv("KEEP_AWAKE_URLS", "").split(",") if u.strip()]
    if explicit:
        return explicit
    out = []
    own = os.getenv("RENDER_EXTERNAL_URL", "").rstrip("/")
    if own:
        out.append(own + "/api/v1/health")
    out += [o.rstrip("/") + "/" for o in cors_origins if o.startswith("https://") and o.rstrip("/") + "/" not in out]
    return out


def enabled() -> bool:
    if os.getenv("KEEP_AWAKE", "").lower() in ("off", "0", "false", "no"):
        return False
    return bool(os.getenv("RENDER") or os.getenv("KEEP_AWAKE_URLS"))


def _ping(url: str) -> str:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "BrandVault-keep-awake/1.0"})
        with urllib.request.urlopen(req, timeout=90) as r:  # noqa: S310 (fixed, configured URLs only)
            return str(r.status)
    except Exception as exc:  # never let a ping failure affect the app
        return f"error: {type(exc).__name__}"


async def run(urls: List[str]) -> None:
    state.update(enabled=True, targets=urls, window=os.getenv("KEEP_AWAKE_WINDOW", "09:00-20:30") + " IST")
    await asyncio.sleep(30)  # let startup finish first
    while True:
        if in_window():
            results = {}
            for u in urls:
                results[u] = await asyncio.to_thread(_ping, u)
            state["last_ping"] = datetime.datetime.utcnow().isoformat() + "Z"
            state["last_results"] = results
            log.info("keep-awake ping: %s", results)
        await asyncio.sleep(INTERVAL_SECONDS)


def start(cors_origins: List[str]) -> Optional[asyncio.Task]:
    if not enabled():
        return None
    urls = targets(cors_origins)
    if not urls:
        return None
    return asyncio.get_running_loop().create_task(run(urls))
