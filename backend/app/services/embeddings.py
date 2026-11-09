"""
Dense text embeddings (Round 3 · Improvement 3).

Providers (EMBEDDING_PROVIDER):
- "local"  — BAAI/bge-small-en-v1.5 via fastembed (ONNX, CPU, ~70 MB model, 384 dims).
             No API key; the model is downloaded once (baked into the Docker image).
- "openai" — any OpenAI-compatible /embeddings endpoint (EMBEDDING_BASE_URL,
             EMBEDDING_API_KEY, EMBEDDING_MODEL).
- "none"   — dense retrieval off; keyword + TF-IDF retrieval still works.
- "auto"   — (default) local when fastembed is installed, otherwise none.

Failures never break retrieval: callers fall back to the sparse methods and the
status endpoint reports why.
"""
from __future__ import annotations

import os
import threading
from typing import List, Optional

import numpy as np

from backend.app.core.config import settings

_lock = threading.Lock()
_provider = None
_error: Optional[str] = None


class LocalProvider:
    def __init__(self):
        from fastembed import TextEmbedding
        self.model_name = settings.EMBEDDING_MODEL or "BAAI/bge-small-en-v1.5"
        self.name = f"local:{self.model_name.split('/')[-1]}"
        self._m = TextEmbedding(model_name=self.model_name, cache_dir=settings.EMBEDDING_CACHE_DIR or None)
        self.dim = len(next(iter(self._m.embed(["probe"]))))

    def embed_documents(self, texts: List[str]) -> np.ndarray:
        with _lock:
            return np.array(list(self._m.embed(texts)), dtype=np.float32)

    def embed_query(self, text: str) -> np.ndarray:
        with _lock:
            return np.array(list(self._m.query_embed([text]))[0], dtype=np.float32)


class OpenAICompatProvider:
    def __init__(self):
        import httpx
        self._httpx = httpx
        self.base = (settings.EMBEDDING_BASE_URL or "https://api.openai.com/v1").rstrip("/")
        self.model_name = settings.EMBEDDING_MODEL or "text-embedding-3-small"
        self.name = f"api:{self.model_name}"
        if not settings.EMBEDDING_API_KEY:
            raise RuntimeError("EMBEDDING_API_KEY is not set")
        self.dim = len(self._call(["probe"])[0])

    def _call(self, texts: List[str]) -> List[List[float]]:
        r = self._httpx.post(f"{self.base}/embeddings", json={"model": self.model_name, "input": texts},
                             headers={"Authorization": f"Bearer {settings.EMBEDDING_API_KEY}"}, timeout=30)
        r.raise_for_status()
        return [d["embedding"] for d in sorted(r.json()["data"], key=lambda d: d["index"])]

    def embed_documents(self, texts: List[str]) -> np.ndarray:
        out: List[List[float]] = []
        for i in range(0, len(texts), 64):
            out += self._call(texts[i:i + 64])
        return np.array(out, dtype=np.float32)

    def embed_query(self, text: str) -> np.ndarray:
        return np.array(self._call([text])[0], dtype=np.float32)


def get_provider():
    """The configured provider, or None when dense retrieval is off or unavailable."""
    global _provider, _error
    if _provider is not None or _error is not None:
        return _provider
    choice = (settings.EMBEDDING_PROVIDER or "auto").lower()
    if choice == "none":
        _error = "Dense retrieval is turned off (EMBEDDING_PROVIDER=none)."
        return None
    with _lock:
        if _provider is None and _error is None:
            try:
                if choice == "openai":
                    _provider = OpenAICompatProvider()
                else:  # auto | local
                    _provider = LocalProvider()
            except Exception as exc:  # missing package, no network for the first download, bad key…
                _error = f"{type(exc).__name__}: {str(exc)[:200]}"
    return _provider


def status() -> dict:
    p = get_provider()
    if p:
        return {"available": True, "provider": p.name, "dim": p.dim}
    return {"available": False, "provider": None, "reason": _error}


def reset() -> None:
    """Forget the cached provider (tests / config changes)."""
    global _provider, _error
    _provider, _error = None, None


def normalise(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v, axis=-1, keepdims=True)
    n[n == 0] = 1.0
    return v / n
