"""Dense chunk embeddings (Improvement 3). Portable JSON copy on every database; on
PostgreSQL with pgvector a native `chunk_vectors` table with an HNSW index is kept too."""
import datetime

from sqlalchemy import JSON, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class ChunkEmbedding(Base):
    __tablename__ = "chunk_embeddings"

    chunk_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    org_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    model: Mapped[str] = mapped_column(String(120), nullable=False)
    dim: Mapped[int] = mapped_column(Integer, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    vector: Mapped[list] = mapped_column(JSON, nullable=False)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
