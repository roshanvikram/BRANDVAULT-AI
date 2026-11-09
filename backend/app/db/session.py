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

engine = create_engine(
    _url,
    connect_args=connect_args,
    echo=False,
    # Hosted Postgres (Neon, Supabase) closes idle connections; check before use.
    pool_pre_ping=not _url.startswith("sqlite"),
    pool_recycle=300,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

