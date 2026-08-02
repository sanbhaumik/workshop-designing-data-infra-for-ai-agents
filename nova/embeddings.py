"""Frozen embeddings: pre-computed vectors looked up by content hash, plus a
pure-numpy cosine similarity search over them.
"""
import hashlib
from pathlib import Path

import numpy as np


class EmbeddingMissing(Exception):
    """Raised when no recorded embedding exists for a given text."""


def _key(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def embed(text: str, fixtures_dir: Path) -> np.ndarray:
    """Frozen: return the pre-computed vector for `text`. Raises EmbeddingMissing if absent."""
    path = Path(fixtures_dir) / f"{_key(text)}.npy"
    if not path.exists():
        raise EmbeddingMissing(
            f"no frozen embedding for text hash {_key(text)!r} (expected {path})"
        )
    return np.load(path)


def search(query_vec: np.ndarray, doc_vecs: np.ndarray, k: int) -> list[int]:
    """Cosine similarity, top-k indices into `doc_vecs`, best match first."""
    query_norm = np.linalg.norm(query_vec)
    doc_norms = np.linalg.norm(doc_vecs, axis=1)
    denom = doc_norms * query_norm
    denom[denom == 0] = 1e-12
    similarities = (doc_vecs @ query_vec) / denom
    top_k = np.argsort(-similarities)[:k]
    return [int(i) for i in top_k]
