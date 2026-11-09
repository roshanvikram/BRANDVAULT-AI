"""Shared helpers for the test suite and the evaluation runner.

Builds a fully-seeded throwaway SQLite database (NOVA TECH brand, demo users,
RAG embeddings) so tests and the eval run against the same ground truth the app
ships with, in isolation from the real brandvault.db.
"""
import os
import tempfile
import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.db.base import Base
import backend.app.models  # noqa: F401  (register all models)
from backend.app.db import migrations
from backend.app.services.seed import seed_sample_brand, augment_integrity_demo, seed_demo_users
from backend.app.services.rag import RagRetriever
from backend.app.models.brand import Organization


def make_seeded_db():
    """Return (engine, SessionFactory, db_path). Caller removes db_path when done.

    Set BV_TEST_DATABASE_URL (e.g. a PostgreSQL URL) to run the same tests on
    another database; its tables are dropped and rebuilt for every call.
    """
    pg_url = os.getenv("BV_TEST_DATABASE_URL")
    if pg_url:
        engine = create_engine(pg_url, pool_pre_ping=True, connect_args={"prepare_threshold": None})
        Base.metadata.drop_all(engine)
        path = None
    else:
        path = os.path.join(tempfile.gettempdir(), f"bv_test_{uuid.uuid4().hex}.db")
        engine = create_engine(f"sqlite:///{path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    migrations.run_light_migrations(engine)
    Session = sessionmaker(bind=engine)

    db = Session()
    try:
        seed_sample_brand(db)
        augment_integrity_demo(db)
        seed_demo_users(db)
        retriever = RagRetriever(db)
        for org in db.query(Organization).all():
            retriever.index_org(org.id)
    finally:
        db.close()
    return engine, Session, path


def drop_db(engine, path):
    try:
        engine.dispose()
    finally:
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                pass
