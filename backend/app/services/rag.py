"""
Retrieval-Augmented Generation layer for BRANDVAULT AI (Milestone C).

What this is, honestly:
- Real vector-space retrieval over persisted `document_chunks`: each chunk is
  embedded as an L2-normalized TF-IDF sparse vector; queries are embedded the
  same way; ranking is brute-force cosine similarity combined with a keyword
  overlap score (hybrid retrieval). Results are filtered by organisation and
  guideline status (tenant isolation).
- This is a *statistical* embedding (TF-IDF), not a neural sentence embedding.
  It is deterministic, offline, and dependency-free — a genuine improvement over
  plain token-overlap (IDF weighting + cosine normalisation), but it is not a
  semantic transformer model. Labelled as such everywhere it surfaces.

Swap path (Roadmap): the `Embedder` interface and `RagRetriever` are written so a
neural embedder (sentence-transformers / provider embeddings) or a pgvector-backed
store can replace the default without changing callers — implement `Embedder.embed`
and the vector persistence, keep the same `search()` contract.
"""
from __future__ import annotations

import json
import math
import re
from collections import Counter
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from backend.app.models.brand import DocumentChunk, BrandGuideline

_TOKEN_RE = re.compile(r"[a-z0-9']+")
_ACTIVE_STATUSES = ("processed", "active", "uploaded")


def tokenize(text: str) -> List[str]:
    return _TOKEN_RE.findall((text or "").lower())


class Embedder:
    """Embedder interface. Returns an L2-normalized sparse vector (token -> weight)."""
    name: str = "base"

    def embed(self, text: str, idf: Dict[str, float]) -> Dict[str, float]:
        raise NotImplementedError


class TfidfEmbedder(Embedder):
    """TF-IDF embedder: sublinear TF * IDF, L2-normalized. Keyed by token for
    reproducible persistence (no per-process hash salt)."""
    name = "tfidf"

    def embed(self, text: str, idf: Dict[str, float]) -> Dict[str, float]:
        tokens = tokenize(text)
        if not tokens:
            return {}
        tf = Counter(tokens)
        default_idf = max(idf.values()) if idf else 1.0
        vec: Dict[str, float] = {}
        for term, count in tf.items():
            weight = (1.0 + math.log(count)) * idf.get(term, default_idf)
            if weight:
                vec[term] = weight
        norm = math.sqrt(sum(w * w for w in vec.values()))
        if norm == 0:
            return {}
        return {t: w / norm for t, w in vec.items()}


def cosine(a: Dict[str, float], b: Dict[str, float]) -> float:
    """Dot product of two L2-normalized sparse vectors == cosine similarity."""
    if not a or not b:
        return 0.0
    # iterate the smaller dict
    if len(a) > len(b):
        a, b = b, a
    return sum(w * b.get(t, 0.0) for t, w in a.items())


class RagRetriever:
    def __init__(self, db: Session, embedder: Optional[Embedder] = None, keyword_weight: float = 0.35):
        self.db = db
        self.embedder = embedder or TfidfEmbedder()
        self.keyword_weight = keyword_weight

    def _corpus(self, org_id: str) -> List[DocumentChunk]:
        """Org-isolated, status-filtered chunk corpus."""
        return (
            self.db.query(DocumentChunk)
            .join(DocumentChunk.guideline)
            .filter(
                DocumentChunk.guideline.has(org_id=org_id),
                DocumentChunk.guideline.has(BrandGuideline.status.in_(_ACTIVE_STATUSES)),
            )
            .all()
        )

    def _build_idf(self, chunks: List[DocumentChunk]) -> Dict[str, float]:
        n = len(chunks)
        df: Counter = Counter()
        for ch in chunks:
            for term in set(tokenize(ch.content)):
                df[term] += 1
        # smoothed idf, always >= 1
        return {term: math.log((1 + n) / (1 + d)) + 1.0 for term, d in df.items()}

    def _vectorize_corpus(self, org_id: str) -> Tuple[Dict[str, float], List[Tuple[DocumentChunk, Dict[str, float]]]]:
        chunks = self._corpus(org_id)
        idf = self._build_idf(chunks)
        vectors = [(ch, self.embedder.embed(ch.content, idf)) for ch in chunks]
        return idf, vectors

    def index_org(self, org_id: str) -> int:
        """Persist each chunk's embedding into document_chunks.embedding_json.
        Returns the number of chunks indexed. Satisfies 'store vectors'."""
        idf, vectors = self._vectorize_corpus(org_id)
        count = 0
        for ch, vec in vectors:
            payload = {
                "embedder": self.embedder.name,
                "dims": len(vec),
                # round to keep the stored vector compact
                "vector": {t: round(w, 5) for t, w in sorted(vec.items(), key=lambda kv: -kv[1])[:40]},
            }
            ch.embedding_json = json.dumps(payload)
            count += 1
        self.db.commit()
        try:
            self._dense_index(org_id, [ch for ch, _ in vectors])
        except Exception as exc:  # dense index is an enhancement; sparse retrieval still works
            print(f"[rag] dense index skipped for {org_id}: {exc}")
        return count

    # --------------------------------------------------------- dense index --
    def _dense_index(self, org_id: str, chunks: List[DocumentChunk]) -> int:
        """Embed chunks whose text or model changed. Returns how many were (re)embedded."""
        from backend.app.models.retrieval import ChunkEmbedding
        from backend.app.services import embeddings as emb
        prov = emb.get_provider()
        if prov is None or not chunks:
            return 0
        have = {e.chunk_id: e for e in self.db.query(ChunkEmbedding).filter(ChunkEmbedding.org_id == org_id).all()}
        todo = [ch for ch in chunks
                if ch.id not in have or have[ch.id].model != prov.name or have[ch.id].content_hash != _hash(ch.content)]
        if todo:
            vecs = emb.normalise(prov.embed_documents([ch.content for ch in todo]))
            for ch, v in zip(todo, vecs):
                row = have.get(ch.id) or ChunkEmbedding(chunk_id=ch.id, org_id=org_id)
                row.model, row.dim, row.content_hash = prov.name, int(v.shape[0]), _hash(ch.content)
                row.vector = [round(float(x), 6) for x in v]
                self.db.add(row)
            self.db.commit()
        _pgvector_sync(self.db, org_id, prov.name)
        return len(todo)

    def _dense_scores(self, org_id: str, query: str, chunk_ids: List[str]) -> Dict[str, float]:
        """Cosine similarity of the query to each chunk (pgvector when available, else exact numpy)."""
        from backend.app.models.retrieval import ChunkEmbedding
        from backend.app.services import embeddings as emb
        prov = emb.get_provider()
        if prov is None:
            return {}
        try:
            q = emb.normalise(prov.embed_query(query))
        except Exception:
            return {}
        wanted = set(chunk_ids)
        native = _pgvector_search(self.db, org_id, prov.name, q, limit=50)
        if native is not None:
            return {cid: sim for cid, sim in native if cid in wanted}
        rows = (self.db.query(ChunkEmbedding)
                .filter(ChunkEmbedding.org_id == org_id, ChunkEmbedding.model == prov.name,
                        ChunkEmbedding.chunk_id.in_(chunk_ids)).all())
        if not rows:
            return {}
        import numpy as np
        mat = np.array([r.vector for r in rows], dtype=np.float32)
        sims = mat @ q
        return {r.chunk_id: float(x) for r, x in zip(rows, sims)}

    # -------------------------------------------------------------- search --
    def search(self, org_id: str, query: str, top_k: int = 3) -> List[Dict]:
        """Org-isolated retrieval.

        hybrid (default): BM25 + TF-IDF cosine + dense embedding similarity, fused
        with Reciprocal Rank Fusion. A passage found only by meaning (dense) must
        clear DENSE_MIN so unrelated text is never cited as evidence.
        tfidf: the Round 2 method (TF-IDF cosine + keyword overlap), kept as a baseline.
        """
        from backend.app.core.config import settings
        idf, vectors = self._vectorize_corpus(org_id)
        if not vectors:
            return []
        q_vec = self.embedder.embed(query, idf)
        q_tokens = set(tokenize(query))
        base = {}
        for ch, c_vec in vectors:
            cos = cosine(q_vec, c_vec)
            c_tokens = set(tokenize(ch.content))
            kw = (len(q_tokens & c_tokens) / len(q_tokens)) if q_tokens else 0.0
            base[ch.id] = (ch, cos, kw, (1 - self.keyword_weight) * cos + self.keyword_weight * kw)

        mode = (settings.RAG_MODE or "hybrid").lower()
        if mode == "tfidf":
            ranked = sorted((v for v in base.values() if v[3] > 0), key=lambda v: v[3], reverse=True)
            return [self._result(ch, score, cos, kw, method="tfidf") for ch, cos, kw, score in ranked[:top_k]]

        chunks = [v[0] for v in base.values()]
        bm = {ch.id: sc for ch, sc in zip(chunks, bm25_scores(query, [ch.content for ch in chunks]))}
        dense = self._dense_scores(org_id, query, [ch.id for ch in chunks])
        # Two-stage RRF: TF-IDF and BM25 are both lexical (highly correlated), so they are fused
        # into one lexical ranking first; that ranking and the dense ranking then get one vote each.
        lex_rrf = _rrf([{cid: v[3] for cid, v in base.items()}, bm])
        dense_ok = {cid: s for cid, s in dense.items() if s >= DENSE_MIN or lex_rrf.get(cid)}
        fused = _rrf([lex_rrf, dense_ok])
        ranked = sorted(fused.items(), key=lambda kv: kv[1], reverse=True)[:top_k]
        method = "hybrid-rrf (bm25 + tfidf" + (f" + dense:{_provider_name()})" if dense else ")")
        return [self._result(base[cid][0], round(f * 100, 4), base[cid][1], base[cid][2], method=method,
                             bm25=bm.get(cid, 0.0), dense=dense.get(cid)) for cid, f in ranked]

    def _result(self, ch: DocumentChunk, score: float, cos: float, kw: float, method: str,
                bm25: Optional[float] = None, dense: Optional[float] = None) -> Dict:
        guideline = ch.guideline
        filename = guideline.filename if guideline else "Brand Guideline"
        out = {"chunk_id": ch.id, "filename": filename, "page": ch.page_number, "content": ch.content,
               "citation": f"{filename} ({ch.section_label or f'Page {ch.page_number}'})", "score": round(score, 4),
               "cosine": round(cos, 4), "keyword": round(kw, 4), "embedder": self.embedder.name, "retrieval": method}
        if bm25 is not None:
            out["bm25"] = round(bm25, 4)
        if dense is not None:
            out["dense"] = round(dense, 4)
        return out

    def best(self, org_id: str, query: str) -> Optional[Dict]:
        hits = self.search(org_id, query, top_k=1)
        return hits[0] if hits else None


# ------------------------------------------------------------------ helpers --
RRF_K = 60          # standard Reciprocal Rank Fusion constant
DENSE_MIN = 0.62    # meaning-only matches below this cosine are not treated as evidence
_BM25_K1, _BM25_B = 1.5, 0.75


def _rrf(score_maps: List[Dict[str, float]]) -> Dict[str, float]:
    """Reciprocal Rank Fusion over score maps (only positive scores rank)."""
    fused: Dict[str, float] = {}
    for scores in score_maps:
        ordered = [cid for cid, sc in sorted(scores.items(), key=lambda kv: kv[1], reverse=True) if sc > 0]
        for rank, cid in enumerate(ordered, 1):
            fused[cid] = fused.get(cid, 0.0) + 1.0 / (RRF_K + rank)
    return fused


def _hash(text: str) -> str:
    import hashlib
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def _provider_name() -> str:
    from backend.app.services import embeddings as emb
    p = emb.get_provider()
    return p.name if p else "none"


def bm25_scores(query: str, docs: List[str]) -> List[float]:
    """Okapi BM25 over the given documents (exact-term relevance, length-normalised)."""
    toks = [tokenize(d) for d in docs]
    n = len(toks)
    if not n:
        return []
    avgdl = (sum(len(t) for t in toks) / n) or 1.0
    df: Counter = Counter()
    for t in toks:
        df.update(set(t))
    q = tokenize(query)
    out = []
    for t in toks:
        tf = Counter(t)
        dl = len(t) or 1
        score = 0.0
        for term in q:
            f = tf.get(term, 0)
            if not f:
                continue
            idf = math.log(1 + (n - df[term] + 0.5) / (df[term] + 0.5))
            score += idf * f * (_BM25_K1 + 1) / (f + _BM25_K1 * (1 - _BM25_B + _BM25_B * dl / avgdl))
        out.append(score)
    return out


def _is_pg(db: Session) -> bool:
    return db.get_bind().dialect.name == "postgresql"


_PGV_READY: Dict[str, bool] = {}


def _pgvector_ready(db: Session, dim: int) -> bool:
    """Create the native pgvector table + HNSW index once, if the extension is available."""
    if not _is_pg(db):
        return False
    key = f"{db.get_bind().url}:{dim}"
    if key in _PGV_READY:
        return _PGV_READY[key]
    from sqlalchemy import text
    try:  # on the session's own connection (no second connection that could wait on this one)
        db.commit()
        db.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        db.execute(text(f"CREATE TABLE IF NOT EXISTS chunk_vectors (chunk_id varchar(36) PRIMARY KEY, "
                        f"org_id varchar(36) NOT NULL, model varchar(120) NOT NULL, embedding vector({dim}) NOT NULL)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_chunk_vectors_org ON chunk_vectors (org_id, model)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_chunk_vectors_hnsw ON chunk_vectors USING hnsw (embedding vector_cosine_ops)"))
        db.commit()
        _PGV_READY[key] = True
    except Exception as exc:
        db.rollback()
        print(f"[rag] pgvector unavailable, using portable vectors: {str(exc)[:160]}")
        _PGV_READY[key] = False
    return _PGV_READY[key]


def _vec_literal(values) -> str:
    return "[" + ",".join(str(float(x)) for x in values) + "]"


def _pgvector_sync(db: Session, org_id: str, model: str) -> None:
    from backend.app.models.retrieval import ChunkEmbedding
    rows = db.query(ChunkEmbedding).filter(ChunkEmbedding.org_id == org_id, ChunkEmbedding.model == model).all()
    if not rows or not _pgvector_ready(db, rows[0].dim):
        return
    from sqlalchemy import text
    try:
        db.execute(text("DELETE FROM chunk_vectors WHERE org_id = :o"), {"o": org_id})
        for r in rows:
            db.execute(text("INSERT INTO chunk_vectors (chunk_id, org_id, model, embedding) "
                            "VALUES (:c, :o, :m, CAST(:e AS vector))"),
                       {"c": r.chunk_id, "o": org_id, "m": model, "e": _vec_literal(r.vector)})
        db.commit()
    except Exception as exc:
        db.rollback()
        print(f"[rag] pgvector sync skipped: {str(exc)[:160]}")


def _pgvector_search(db: Session, org_id: str, model: str, q, limit: int = 50):
    """Nearest chunks by cosine via pgvector, or None when the native path is not in use."""
    if not _is_pg(db) or not any(_PGV_READY.values()):
        return None
    from sqlalchemy import text
    try:
        rows = db.execute(text("SELECT chunk_id, 1 - (embedding <=> CAST(:q AS vector)) AS sim FROM chunk_vectors "
                               "WHERE org_id = :o AND model = :m ORDER BY embedding <=> CAST(:q AS vector) LIMIT :k"),
                          {"q": _vec_literal(q), "o": org_id, "m": model, "k": limit}).fetchall()
        return [(r[0], float(r[1])) for r in rows]
    except Exception:
        db.rollback()
        return None
