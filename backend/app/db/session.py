from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.core.config import settings

connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
elif settings.DATABASE_URL.startswith(("postgres", "postgresql")):
    # No server-side prepared statements: safe behind PgBouncer-style poolers
    # (e.g. Neon's "-pooler" endpoint) that share one backend between clients.
    connect_args = {"prepare_threshold": None}

_url = settings.DATABASE_URL
if _url.startswith("postgres://"):  # some hosts hand out the legacy scheme
    _url = "postgresql://" + _url[len("postgres://"):]

# Fail-safe local fallback: if PostgreSQL is configured but unreachable (e.g. offline dev,
# missing DNS, or network sandbox), smoothly fall back to SQLite within 1.5s so tests & dev never hang.
if _url.startswith("postgresql"):
    host = None
    port = 5432
    try:
        from urllib.parse import urlparse
        parsed = urlparse(_url)
        host = parsed.hostname
        port = parsed.port or 5432
    except Exception:
        pass
    
    reachable = False
    if host:
        import socket
        try:
            s = socket.create_connection((host, port), timeout=1.5)
            s.close()
            reachable = True
        except Exception:
            reachable = False
            
    if not reachable:
        import logging
        logging.getLogger("uvicorn.error").warning(
            f"PostgreSQL host '{host}' unreachable. Falling back to SQLite local database."
        )
        _url = "sqlite:///./brandvault.db"
        connect_args = {"check_same_thread": False}

engine = create_engine(
    _url,
    connect_args=connect_args,
    echo=False,
    # Hosted Postgres (Neon, Supabase) closes idle connections; check before use.
    pool_pre_ping=not _url.startswith("sqlite"),
    pool_recycle=300,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Schema changes at startup (create tables, add columns, Row-Level Security policies)
# go over a direct connection when one is configured: Neon recommends running DDL
# outside its connection pooler. Falls back to the normal engine.
_ddl_url = settings.DATABASE_URL_UNPOOLED or ""
if _ddl_url.startswith("postgres://"):
    _ddl_url = "postgresql://" + _ddl_url[len("postgres://"):]
ddl_engine = (create_engine(_ddl_url, connect_args=connect_args, pool_pre_ping=True, pool_size=1, max_overflow=1)
              if _ddl_url.startswith("postgresql") and _url.startswith("postgresql") else engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

