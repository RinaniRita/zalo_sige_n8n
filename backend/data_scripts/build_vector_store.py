"""
build_vector_store.py
=====================
Builds FAISS vector index from chunks produced by chunk_kb.process_kb_folder.

Saves to data/vector_store/:
  - faiss_index.index
  - metadata.json
  - embeddings.npy
"""

import os
import json
import time
import logging
from pathlib import Path
from typing import List, Dict

import numpy as np
import faiss
from dotenv import load_dotenv
from openai import OpenAI

# Load env vars (finds .env up the tree)
load_dotenv(dotenv_path=Path(__file__).parent.parent.parent / ".env", override=True)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("build_vector_store")

# ---------- CONFIG ----------
KB_FOLDER    = Path(__file__).parent.parent / "knowlege_base"   # <-- where .md files live
VECTOR_DIR   = Path(__file__).parent.parent.parent / "data" / "vector_store"
VECTOR_DIR.mkdir(parents=True, exist_ok=True)

OPENAI_API_KEY     = os.getenv("OPENAI_API_KEY")
EMBED_MODEL        = "text-embedding-3-small"
EMBED_DIMENSION    = 1536  # output dim of text-embedding-3-small
# ----------------------------

client = OpenAI(api_key=OPENAI_API_KEY)

# Relative import (package) or direct when run as __main__
try:
    from .chunk_kb import process_kb_folder
except ImportError:
    from chunk_kb import process_kb_folder


# ─── Embedding ───────────────────────────────────────────────────────────────

def get_embedding(text: str) -> List[float]:
    """Call OpenAI Embeddings API with retry on rate-limit."""
    for attempt in range(3):
        try:
            response = client.embeddings.create(model=EMBED_MODEL, input=text)
            return response.data[0].embedding
        except Exception as e:
            if attempt < 2:
                wait = 2 ** attempt
                logger.warning(f"Embedding attempt {attempt+1} failed ({e}). Retrying in {wait}s...")
                time.sleep(wait)
            else:
                raise


# ─── FAISS ───────────────────────────────────────────────────────────────────

def build_faiss_index(vectors: np.ndarray) -> faiss.Index:
    """Normalize vectors and build an IndexFlatIP (cosine similarity)."""
    faiss.normalize_L2(vectors)
    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)
    return index


def save_artifacts(index: faiss.Index, vectors: np.ndarray, metadata_list: List[Dict]):
    idx_path  = VECTOR_DIR / "faiss_index.index"
    meta_path = VECTOR_DIR / "metadata.json"
    emb_path  = VECTOR_DIR / "embeddings.npy"

    faiss.write_index(index, str(idx_path))
    logger.info(f"FAISS index saved → {idx_path}")

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata_list, f, ensure_ascii=False, indent=2)
    logger.info(f"Metadata saved   → {meta_path}  ({len(metadata_list)} entries)")

    np.save(str(emb_path), vectors)
    logger.info(f"Embeddings saved → {emb_path}")


# ─── Orchestrator ────────────────────────────────────────────────────────────

def build_from_chunks(chunks: List[Dict]):
    """Embed all chunks and write FAISS artifacts."""
    logger.info(f"Generating embeddings for {len(chunks)} chunks via OpenAI ({EMBED_MODEL})...")

    vectors: List[List[float]] = []
    metadata_list: List[Dict] = []
    failed = 0
    start = time.time()

    for i, chunk in enumerate(chunks):
        text = chunk["text"]
        try:
            emb = get_embedding(text)
            vectors.append(emb)
            metadata_list.append({
                "id":           chunk["id"],
                "text_snippet": text,
                "metadata":     chunk.get("metadata", {}),
            })
            if (i + 1) % 10 == 0:
                logger.info(f"  Embedded {i+1}/{len(chunks)} chunks...")
        except Exception as e:
            logger.error(f"  Skipped chunk '{chunk['id']}': {e}")
            failed += 1

    if not vectors:
        raise RuntimeError("No embeddings were generated. Check OPENAI_API_KEY and network.")

    arr = np.array(vectors, dtype="float32")
    elapsed = time.time() - start
    logger.info(f"Done — {len(vectors)} vectors (dim={arr.shape[1]}) in {elapsed:.1f}s  [failed={failed}]")

    index = build_faiss_index(arr)
    save_artifacts(index, arr, metadata_list)
    logger.info("✅ Vector store built successfully!")


# ─── Entry Point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if not KB_FOLDER.exists():
        logger.error(f"Knowledge-base folder not found: {KB_FOLDER}")
    else:
        logger.info(f"Reading knowledge base from: {KB_FOLDER}")
        chunks = process_kb_folder(str(KB_FOLDER))
        build_from_chunks(chunks)
