"""
rag_service.py
==============
Loads the FAISS vector index built by data_scripts/build_vector_store.py
and performs similarity search using OpenAI embeddings.

No LangChain dependency — uses faiss-cpu + openai directly.
"""

import os
import json
import logging
from pathlib import Path
from typing import List

import numpy as np
import faiss
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent.parent.parent.parent / ".env", override=True)

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBED_MODEL    = "text-embedding-3-small"

VECTOR_DIR  = Path(__file__).parent.parent.parent.parent / "data" / "vector_store"
IDX_PATH    = VECTOR_DIR / "faiss_index.index"
META_PATH   = VECTOR_DIR / "metadata.json"

client = OpenAI(api_key=OPENAI_API_KEY)

# ── Singletons loaded once at import time ────────────────────────────────────
_index: faiss.Index | None = None
_metadata: list = []


def _load_artifacts():
    global _index, _metadata
    if not IDX_PATH.exists():
        logger.warning("FAISS index not found at %s. Run ingest_sige.py first.", IDX_PATH)
        return
    if not META_PATH.exists():
        logger.warning("Metadata file not found at %s.", META_PATH)
        return

    _index = faiss.read_index(str(IDX_PATH))
    with open(META_PATH, "r", encoding="utf-8") as f:
        _metadata = json.load(f)
    logger.info("FAISS index loaded: %d vectors from %s", _index.ntotal, IDX_PATH)


# Load at module import
_load_artifacts()


# ─── Public API ──────────────────────────────────────────────────────────────

def reload_index():
    """Hot-reload the FAISS index (call after a new ingest)."""
    _load_artifacts()


def retrieve_context(query: str, top_k: int = 3) -> str:
    """
    Embed query → search FAISS → return concatenated top-K text snippets.
    Returns empty string if index is unavailable.
    """
    if _index is None or not _metadata:
        logger.warning("FAISS index not available. Returning empty context.")
        return ""

    try:
        response = client.embeddings.create(model=EMBED_MODEL, input=query)
        query_vec = np.array([response.data[0].embedding], dtype="float32")
        faiss.normalize_L2(query_vec)

        scores, indices = _index.search(query_vec, top_k)

        results: List[str] = []
        for rank, idx in enumerate(indices[0]):
            if idx < 0 or idx >= len(_metadata):
                continue
            entry = _metadata[idx]
            snippet = entry.get("text_snippet", "")
            score   = float(scores[0][rank])
            results.append(f"[Relevance: {score:.3f}]\n{snippet}")

        return "\n\n---\n\n".join(results)

    except Exception as e:
        logger.error("retrieve_context error: %s", e)
        return ""
