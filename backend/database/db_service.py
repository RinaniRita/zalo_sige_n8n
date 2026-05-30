import sqlite3
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# ── DB path: stored inside data/ at the project root ────────────────────────
DB_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "sige_data.db"
)


def get_connection() -> sqlite3.Connection:
    """Open a connection with row_factory and foreign keys enabled."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")   # better concurrent write safety
    return conn


def init_db():
    """Create all tables if they don't exist yet."""
    conn = get_connection()
    try:
        conn.executescript("""
            -- ── Customer leads collected via Zalo bot ──────────────────────
            CREATE TABLE IF NOT EXISTS customer_leads (
                id              TEXT PRIMARY KEY,
                zalo_user_id    TEXT UNIQUE,
                created_date    TEXT DEFAULT (datetime('now')),
                fb_name         TEXT,
                phone           TEXT,
                email           TEXT,
                birth_year      TEXT,
                gpa             TEXT,
                aspiration      TEXT,
                language        TEXT,
                lead_source     TEXT DEFAULT 'zalo_bot',
                degree          TEXT,
                raw_message     TEXT,
                updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- ── Conversation history per Zalo user ──────────────────────────
            CREATE TABLE IF NOT EXISTS conversation_history (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                zalo_user_id    TEXT NOT NULL,
                role            TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
                content         TEXT NOT NULL,
                event_name      TEXT,
                created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- ── Knowledge-base ingest events ────────────────────────────────
            CREATE TABLE IF NOT EXISTS ingest_events (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                source_folder   TEXT NOT NULL,
                num_chunks      INTEGER NOT NULL,
                ingest_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- ── Nudge scheduling state per Zalo user ─────────────────────────
            -- Tracks the 12h / 24h follow-up nudge cycle.
            -- cancelled=1 means the user replied after a nudge was sent;
            -- no new nudge cycle will start for this entry.
            CREATE TABLE IF NOT EXISTS nudge_state (
                zalo_user_id     TEXT PRIMARY KEY,
                last_user_msg_at TIMESTAMP NOT NULL,
                nudge1_sent      INTEGER DEFAULT 0,
                nudge2_sent      INTEGER DEFAULT 0,
                cancelled        INTEGER DEFAULT 0
            );
        """)
        conn.commit()
        logger.info("Database initialised at %s", DB_PATH)
    except Exception as e:
        logger.error("init_db error: %s", e)
        raise
    finally:
        conn.close()


# ─── Customer Leads ──────────────────────────────────────────────────────────

def upsert_lead_from_zalo(lead_data: dict) -> bool:
    """
    Insert or update a lead detected during a Zalo conversation.
    lead_data keys: zalo_user_id, fb_name, phone, email, birth_year,
                    gpa, aspiration, language, degree, raw_message
    """
    conn = get_connection()
    try:
        fields = [
            "zalo_user_id", "fb_name", "phone", "email",
            "birth_year", "gpa", "aspiration", "language", "degree",
            "raw_message",
        ]
        placeholders = ", ".join(["?"] * len(fields))
        update_set = ", ".join(
            [f"{f} = COALESCE(excluded.{f}, {f})" for f in fields if f != "zalo_user_id"]
        )

        # Use zalo_user_id as the PK for bot-sourced leads
        query = f"""
            INSERT INTO customer_leads ({', '.join(fields)})
            VALUES ({placeholders})
            ON CONFLICT(zalo_user_id) DO UPDATE SET
              {update_set},
              updated_at = CURRENT_TIMESTAMP
        """
        values = [lead_data.get(f) for f in fields]
        conn.execute(query, values)
        conn.commit()
        logger.info("Upserted lead for zalo_user_id=%s", lead_data.get("zalo_user_id"))
        return True
    except Exception as e:
        logger.error("upsert_lead_from_zalo error: %s", e)
        return False
    finally:
        conn.close()


def upsert_customer_lead(lead_data: dict) -> bool:
    """
    Insert or update a full customer lead (e.g. synced from Google Sheets).
    Requires 'id' field.
    """
    conn = get_connection()
    try:
        fields = [
            "id", "created_date", "fb_name", "phone", "email",
            "birth_year", "gpa", "aspiration", "language", "lead_source", "degree",
        ]
        placeholders = ", ".join(["?"] * len(fields))
        update_set = ", ".join([f"{f} = excluded.{f}" for f in fields if f != "id"])

        query = f"""
            INSERT INTO customer_leads ({', '.join(fields)})
            VALUES ({placeholders})
            ON CONFLICT(id) DO UPDATE SET
              {update_set},
              updated_at = CURRENT_TIMESTAMP
        """
        values = [lead_data.get(f) for f in fields]
        conn.execute(query, values)
        conn.commit()
        logger.info("Upserted customer lead id=%s", lead_data.get("id"))
        return True
    except Exception as e:
        logger.error("upsert_customer_lead error: %s", e)
        return False
    finally:
        conn.close()


def update_lead_field(lead_id: str, field: str, value) -> bool:
    """Update a single field on a customer lead (safe against SQL injection via PRAGMA check)."""
    conn = get_connection()
    try:
        cursor = conn.execute("PRAGMA table_info(customer_leads)")
        valid_columns = [row[1] for row in cursor.fetchall()]
        if field not in valid_columns:
            logger.error("Invalid column name: %s", field)
            return False

        conn.execute(
            f"""
            INSERT INTO customer_leads (id, {field})
            VALUES (?, ?)
            ON CONFLICT(id) DO UPDATE SET
              {field} = excluded.{field},
              updated_at = CURRENT_TIMESTAMP
            """,
            (lead_id, value),
        )
        conn.commit()
        logger.info("Updated lead id=%s field=%s", lead_id, field)
        return True
    except Exception as e:
        logger.error("update_lead_field error: %s", e)
        return False
    finally:
        conn.close()


def get_customer_lead(lead_id: str) -> dict | None:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM customer_leads WHERE id = ?", (lead_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_lead_by_zalo_id(zalo_user_id: str) -> dict | None:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM customer_leads WHERE zalo_user_id = ?", (zalo_user_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_next_lead_index() -> int:
    conn = get_connection()
    try:
        row = conn.execute("SELECT COUNT(*) FROM customer_leads").fetchone()
        return (row[0] + 1) if row else 1
    finally:
        conn.close()


# ─── Conversation History ────────────────────────────────────────────────────

def add_conversation_turn(zalo_user_id: str, role: str, content: str, event_name: str = None):
    """Append one turn (user or assistant) to the conversation log."""
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO conversation_history (zalo_user_id, role, content, event_name)
            VALUES (?, ?, ?, ?)
            """,
            (zalo_user_id, role, content, event_name),
        )
        conn.commit()
    except Exception as e:
        logger.error("add_conversation_turn error: %s", e)
    finally:
        conn.close()


def get_conversation_history(zalo_user_id: str, limit: int = 10) -> list[dict]:
    """Return last N turns for a given user (oldest first)."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT role, content, created_at FROM conversation_history
            WHERE zalo_user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (zalo_user_id, limit),
        ).fetchall()
        # Return in chronological order
        return [dict(r) for r in reversed(rows)]
    finally:
        conn.close()


def clear_conversation_history(zalo_user_id: str):
    """Wipe conversation history for a user (e.g. on explicit reset command)."""
    conn = get_connection()
    try:
        conn.execute(
            "DELETE FROM conversation_history WHERE zalo_user_id = ?",
            (zalo_user_id,),
        )
        conn.commit()
    finally:
        conn.close()


# ─── Ingest Events ───────────────────────────────────────────────────────────

def record_ingest_event(source_folder: str, num_chunks: int):
    """Log a knowledge-base ingest run into SQLite."""
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO ingest_events (source_folder, num_chunks) VALUES (?, ?)",
            (source_folder, num_chunks),
        )
        conn.commit()
        logger.info("Ingest event recorded: %d chunks from %s", num_chunks, source_folder)
    except Exception as e:
        logger.error("record_ingest_event error: %s", e)
    finally:
        conn.close()


def get_last_ingest() -> dict | None:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM ingest_events ORDER BY ingest_at DESC LIMIT 1"
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


# ─── Nudge State ─────────────────────────────────────────────────────────────

def upsert_nudge_state(zalo_user_id: str) -> None:
    """
    Called every time a user sends a message AND no nudge has been sent yet.
    Resets (or creates) the nudge cycle timer to NOW.
    If a nudge has already been sent the caller must NOT call this — use
    cancel_nudge() instead.
    """
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO nudge_state (zalo_user_id, last_user_msg_at, nudge1_sent, nudge2_sent, cancelled)
            VALUES (?, datetime('now'), 0, 0, 0)
            ON CONFLICT(zalo_user_id) DO UPDATE SET
                last_user_msg_at = datetime('now'),
                nudge1_sent = 0,
                nudge2_sent = 0,
                cancelled = 0
            """,
            (zalo_user_id,),
        )
        conn.commit()
        logger.info("[Nudge] Timer reset for user=%s", zalo_user_id)
    except Exception as e:
        logger.error("upsert_nudge_state error: %s", e)
    finally:
        conn.close()


def cancel_nudge(zalo_user_id: str) -> None:
    """
    Permanently cancel the nudge cycle for a user.
    Called when the user replies AFTER at least one nudge has been sent.
    Sets cancelled=1 so the background scheduler will skip this user forever.
    """
    conn = get_connection()
    try:
        conn.execute(
            """
            UPDATE nudge_state
            SET cancelled = 1
            WHERE zalo_user_id = ?
            """,
            (zalo_user_id,),
        )
        conn.commit()
        logger.info("[Nudge] Cycle permanently cancelled for user=%s", zalo_user_id)
    except Exception as e:
        logger.error("cancel_nudge error: %s", e)
    finally:
        conn.close()


def get_nudge_state(zalo_user_id: str) -> dict | None:
    """Return the current nudge state row for a user, or None if not found."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM nudge_state WHERE zalo_user_id = ?",
            (zalo_user_id,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_pending_nudge_users() -> list[dict]:
    """
    Return all users that:
    - are NOT cancelled
    - still have at least one nudge to send
    """
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT * FROM nudge_state
            WHERE cancelled = 0
              AND (nudge1_sent = 0 OR nudge2_sent = 0)
            """
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def mark_nudge_sent(zalo_user_id: str, nudge_num: int) -> None:
    """Mark nudge 1 or 2 as sent for a user."""
    if nudge_num not in (1, 2):
        logger.error("mark_nudge_sent: invalid nudge_num=%s", nudge_num)
        return
    field = f"nudge{nudge_num}_sent"
    conn = get_connection()
    try:
        conn.execute(
            f"UPDATE nudge_state SET {field} = 1 WHERE zalo_user_id = ?",
            (zalo_user_id,),
        )
        conn.commit()
        logger.info("[Nudge] Marked nudge%d sent for user=%s", nudge_num, zalo_user_id)
    except Exception as e:
        logger.error("mark_nudge_sent error: %s", e)
    finally:
        conn.close()
