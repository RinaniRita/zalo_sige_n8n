"""
start_ingest.py
===============
Entry point: Build/rebuild the FAISS vector store from files in backend/knowlege_base/.

Usage (from project root):
    python start_ingest.py

What it does:
  1. Scans backend/knowlege_base/ for all .md files
  2. Chunks them using backend/data_scripts/chunk_kb.py
  3. Embeds chunks via OpenAI API (text-embedding-3-small)
  4. Saves FAISS index + metadata to data/vector_store/
  5. Records the ingest event in the SQLite database
"""

import sys
import logging
from pathlib import Path

# Ensure project root is on the path
sys.path.insert(0, str(Path(__file__).parent))

from backend.data_scripts.ingest_sige import run_ingestion

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

if __name__ == "__main__":
    run_ingestion()
