"""
start_bot_and_api_server.py
===========================
Entry point: Launch the Zalo Bot webhook server + its internal API.

Usage (from project root):
    python start_bot_and_api_server.py [--port 3000] [--host 0.0.0.0] [--reload]

What it does:
  1. Initialises the SQLite database (creates tables if needed)
  2. Loads the FAISS vector index from data/vector_store/
  3. Starts the FastAPI server (Zalo webhook + internal REST API)
     on http://0.0.0.0:3000 by default

Environment:
  Copy .env and set ZALO_APP_ID, ZALO_SECRET_KEY, ZALO_OA_ACCESS_TOKEN,
  OPENAI_API_KEY, N8N_WEBHOOK_URL before starting.
"""

import sys
import argparse
import logging
from pathlib import Path

import uvicorn

# Ensure project root is importable
sys.path.insert(0, str(Path(__file__).parent))

from backend.database.db_service import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("launcher")


def parse_args():
    parser = argparse.ArgumentParser(description="Zalo Bot & API Server launcher")
    parser.add_argument("--host",   default="0.0.0.0",          help="Bind host (default: 0.0.0.0)")
    parser.add_argument("--port",   default=3000, type=int,      help="Bind port (default: 3000)")
    parser.add_argument("--reload", action="store_true",         help="Enable auto-reload (dev mode)")
    return parser.parse_args()


def main():
    args = parse_args()

    # ── Step 1: ensure SQLite DB is ready ────────────────────────────────────
    logger.info("Initialising SQLite database…")
    init_db()

    # ── Step 2: start FastAPI + Uvicorn ──────────────────────────────────────
    logger.info(
        "Starting Zalo Bot server on http://%s:%d  (reload=%s)",
        args.host, args.port, args.reload,
    )
    uvicorn.run(
        "backend.bot_server.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info",
    )


if __name__ == "__main__":
    main()
