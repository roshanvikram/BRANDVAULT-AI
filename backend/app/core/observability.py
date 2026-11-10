"""Operations: request IDs, structured logs, metrics, error capture and security headers.

* Every response carries ``X-Request-ID`` (taken from the caller or generated), and
  the same ID is in the log line and in any stored error, so a customer's report
  can be matched to the server's record.
* Unhandled errors return a plain 500 with the request ID (no stack trace to the
  browser), are stored in ``error_events`` for administrators, and go to Sentry
  when ``SENTRY_DSN`` is set and sentry-sdk is installed.
* ``/metrics`` exposes Prometheus counters and latency histograms when
  ``METRICS_TOKEN`` is set (scrapers send it as a bearer token).
"""
from __future__ import annotations

import json
import logging
import re
import sys
import threading
import time
import traceback
import uuid
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse

from backend.app.core.config import settings

log = logging.getLogger("brandvault.request")
STARTED = time.time()
_BUCKETS = (0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0)
_lock = threading.Lock()
_requests: Dict[Tuple[str, str, int], int] = defaultdict(int)
_latency: Dict[str, List[int]] = defaultdict(lambda: [0] * (len(_BUCKETS) + 1))
_latency_sum: Dict[str, float] = defaultdict(float)
_recent: List[float] = []  # recent durations for percentiles (bounded)
_errors = {"count": 0}
session_factory = None  # tests point error capture at their own database
_RID = re.compile(r"^[A-Za-z0-9._-]{8,64}$")


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        out = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(record.created)) + "Z",
               "level": record.levelname, "logger": record.name, "msg": record.getMessage()}
        for k in ("request_id", "method", "path", "status", "ms", "org"):
            if hasattr(record, k):
                out[k] = getattr(record, k)
        if record.exc_info:
            out["exc"] = self.formatException(record.exc_info)
        return json.dumps(out, default=str)


def setup_logging() -> None:
    fmt = (settings.LOG_FORMAT or ("json" if settings.ENVIRONMENT.lower() == "production" else "text")).lower()
    root = logging.getLogger()
    if any(getattr(h, "_bv", False) for h in root.handlers):
        return
    h = logging.StreamHandler(sys.stdout)
    h._bv = True  # type: ignore[attr-defined]
    h.setFormatter(_JsonFormatter() if fmt == "json" else logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    root.addHandler(h)
    if root.level == logging.WARNING and (settings.LOG_FORMAT or settings.ENVIRONMENT.lower() == "production"):
        root.setLevel(logging.INFO)


def setup_sentry() -> bool:
    if not settings.SENTRY_DSN:
        return False
    try:
        import sentry_sdk  # type: ignore
        sentry_sdk.init(dsn=settings.SENTRY_DSN, environment=settings.ENVIRONMENT, release=settings.VERSION,
                        traces_sample_rate=0.0, send_default_pii=False)
        return True
    except Exception as exc:  # noqa: BLE001 - optional integration
        logging.getLogger("brandvault").warning("Sentry not started: %s", exc)
        return False


SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Cross-Origin-Opener-Policy": "same-origin",
}


def _route_of(request: Request) -> str:
    r = getattr(request.scope.get("route"), "path", None)
    if not r:
        return "unmatched"
    prefix = settings.API_V1_STR
    if request.url.path.startswith(prefix) and not r.startswith(prefix):
        r = prefix + r  # routes of the included API router are reported without the prefix
    return r


def _observe(method: str, route: str, status: int, seconds: float) -> None:
    with _lock:
        _requests[(method, route, status)] += 1
        b = _latency[route]
        for i, edge in enumerate(_BUCKETS):
            if seconds <= edge:
                b[i] += 1
                break
        else:
            b[-1] += 1
        _latency_sum[route] += seconds
        _recent.append(seconds)
        if len(_recent) > 5000:
            del _recent[:1000]


def _store_error(request: Request, rid: str, exc: BaseException) -> None:
    try:
        from backend.app.db.session import SessionLocal
        from backend.app.models.account import ErrorEvent
        db = (session_factory or SessionLocal)()
        try:
            db.add(ErrorEvent(org_id=getattr(request.state, "org_id", None), request_id=rid, method=request.method,
                              path=request.url.path[:300], error_type=type(exc).__name__[:120],
                              message="".join(traceback.format_exception_only(type(exc), exc)).strip()[:2000]))
            db.commit()
        finally:
            db.close()
    except Exception:  # noqa: BLE001 - never fail the error path
        pass


def install(app: FastAPI) -> None:
    setup_logging()
    setup_sentry()

    @app.middleware("http")
    async def _observe_request(request: Request, call_next):
        incoming = request.headers.get("x-request-id", "")
        rid = incoming if _RID.match(incoming or "") else uuid.uuid4().hex
        request.state.request_id = rid
        t0 = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception as exc:  # noqa: BLE001
            _errors["count"] += 1
            log.exception("unhandled error", extra={"request_id": rid, "method": request.method, "path": request.url.path})
            _store_error(request, rid, exc)
            response = JSONResponse({"detail": "Something went wrong on the server. Quote this reference if you contact support.",
                                     "request_id": rid}, status_code=500)
        dt = time.perf_counter() - t0
        route = _route_of(request)
        _observe(request.method, route, response.status_code, dt)
        response.headers["X-Request-ID"] = rid
        for k, v in SECURITY_HEADERS.items():
            response.headers.setdefault(k, v)
        if settings.ENVIRONMENT.lower() == "production":
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        if route not in ("/api/v1/health", "/metrics") or response.status_code >= 400:
            log.info("%s %s %s %.0fms", request.method, route, response.status_code, dt * 1000,
                     extra={"request_id": rid, "method": request.method, "path": route,
                            "status": response.status_code, "ms": round(dt * 1000, 1),
                            "org": getattr(request.state, "org_id", None)})
        return response

    @app.get("/metrics", include_in_schema=False)
    def metrics(request: Request):
        token = settings.METRICS_TOKEN
        if not token:
            return PlainTextResponse("metrics are off (set METRICS_TOKEN)", status_code=404)
        import hmac
        got = request.headers.get("authorization", "").removeprefix("Bearer ").strip()
        if not hmac.compare_digest(got, token):
            return PlainTextResponse("unauthorized", status_code=401)
        return PlainTextResponse(prometheus_text(), media_type="text/plain; version=0.0.4")


def _esc(v: str) -> str:
    return v.replace("\\", "\\\\").replace('"', '\\"')


def prometheus_text() -> str:
    lines = ["# HELP brandvault_requests_total HTTP requests by route and status.",
             "# TYPE brandvault_requests_total counter"]
    with _lock:
        for (m, r, s), n in sorted(_requests.items()):
            lines.append(f'brandvault_requests_total{{method="{m}",route="{_esc(r)}",status="{s}"}} {n}')
        lines += ["# HELP brandvault_request_seconds Request duration.", "# TYPE brandvault_request_seconds histogram"]
        for r, b in sorted(_latency.items()):
            acc = 0
            for edge, n in zip(_BUCKETS, b):
                acc += n
                lines.append(f'brandvault_request_seconds_bucket{{route="{_esc(r)}",le="{edge}"}} {acc}')
            acc += b[-1]
            lines.append(f'brandvault_request_seconds_bucket{{route="{_esc(r)}",le="+Inf"}} {acc}')
            lines.append(f'brandvault_request_seconds_sum{{route="{_esc(r)}"}} {_latency_sum[r]:.4f}')
            lines.append(f'brandvault_request_seconds_count{{route="{_esc(r)}"}} {acc}')
    lines += ["# TYPE brandvault_unhandled_errors_total counter", f"brandvault_unhandled_errors_total {_errors['count']}",
              "# TYPE brandvault_uptime_seconds gauge", f"brandvault_uptime_seconds {time.time() - STARTED:.0f}"]
    return "\n".join(lines) + "\n"


def snapshot() -> dict:
    """Numbers for the in-app System status view."""
    with _lock:
        total = sum(_requests.values())
        server_err = sum(n for (_, _, s), n in _requests.items() if s >= 500)
        client_err = sum(n for (_, _, s), n in _requests.items() if 400 <= s < 500)
        per_route: Dict[str, int] = defaultdict(int)
        for (_, r, _), n in _requests.items():
            per_route[r] += n
        rec = sorted(_recent)

    def pct(p: float) -> Optional[float]:
        return round(rec[min(len(rec) - 1, int(p * len(rec)))] * 1000, 1) if rec else None

    busiest = sorted(per_route.items(), key=lambda kv: -kv[1])[:8]
    slowest = sorted(((r, _latency_sum[r] / max(1, per_route[r])) for r in per_route if per_route[r] >= 3),
                     key=lambda kv: -kv[1])[:5]
    return {"uptime_seconds": int(time.time() - STARTED), "requests": total, "server_errors": server_err,
            "client_errors": client_err, "error_rate": round(server_err / total, 4) if total else 0.0,
            "latency_ms": {"p50": pct(0.5), "p95": pct(0.95), "p99": pct(0.99)},
            "busiest_routes": [{"route": r, "requests": n} for r, n in busiest],
            "slowest_routes": [{"route": r, "avg_ms": round(a * 1000, 1)} for r, a in slowest],
            "sentry": bool(settings.SENTRY_DSN), "metrics_endpoint": bool(settings.METRICS_TOKEN)}
