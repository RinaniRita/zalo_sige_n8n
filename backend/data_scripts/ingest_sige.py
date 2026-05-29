"""
ingest_sige.py
==============
Full ingestion pipeline orchestrator for the SIGE Knowledge Base.

Steps:
  1. chunk_kb    — scan knowlege_base/ → chunk all .md files
  2. build_vs    — embed chunks with OpenAI → save FAISS artifacts
  3. db_service  — init SQLite DB and record ingest event
"""

import sys
import logging
from pathlib import Path

# Allow running from project root or backend/
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.data_scripts.chunk_kb import process_kb_folder
from backend.data_scripts.build_vector_store import build_from_chunks, KB_FOLDER
from backend.database.db_service import init_db, record_ingest_event

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("ingest_sige")


def run_ingestion():
    # ── Step 0: ensure SQLite DB exists ──────────────────────────────────────
    logger.info("Step 0 — Initialising SQLite database…")
    init_db()

    # ── Step 1: chunk knowledge base ─────────────────────────────────────────
    if not KB_FOLDER.exists():
        logger.error("Knowledge-base folder not found: %s", KB_FOLDER)
        sys.exit(1)

    logger.info("Step 1 — Chunking knowledge base at: %s", KB_FOLDER)
    chunks = process_kb_folder(str(KB_FOLDER))
    logger.info("         %d chunks produced.", len(chunks))

    if not chunks:
        logger.error("No chunks were produced. Aborting.")
        sys.exit(1)

    # ── Step 2: embed & build FAISS index ────────────────────────────────────
    logger.info("Step 2 — Building vector store…")
    build_from_chunks(chunks)

    # ── Step 3: record ingest event in SQLite ────────────────────────────────
    logger.info("Step 3 — Recording ingest event in SQLite…")
    record_ingest_event(
        source_folder=str(KB_FOLDER),
        num_chunks=len(chunks),
    )

    logger.info("✅ Ingestion complete!")


if __name__ == "__main__":
    run_ingestion()
