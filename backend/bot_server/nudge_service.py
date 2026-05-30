"""
nudge_service.py
================
Background async scheduler that sends timed follow-up nudge messages
to Zalo users who have not replied after their last message.

Schedule:
  - Nudge 1 → 12 hours after user's last message
  - Nudge 2 → 24 hours after user's last message

Rules:
  - Each nudge is sent at most ONCE per cycle.
  - If the user replies AFTER a nudge has been sent, the cycle is
    permanently cancelled (cancelled=1 in nudge_state). No new cycle starts.
  - If the user replies BEFORE any nudge has been sent, the timer resets
    normally (new 12h/24h window begins).
"""

import asyncio
import logging
from datetime import datetime, timezone

from backend.database.db_service import (
    get_pending_nudge_users,
    mark_nudge_sent,
)

logger = logging.getLogger(__name__)

# ── Nudge intervals ───────────────────────────────────────────────────────────
NUDGE_1_HOURS = 12
NUDGE_2_HOURS = 24

# How often the scheduler wakes up to check (seconds)
POLL_INTERVAL_SECONDS = 5 * 60  # 5 minutes

# ── Message texts ─────────────────────────────────────────────────────────────
NUDGE_1_TEXT = (
    "Dạ, không biết anh/chị còn thắc mắc gì về chương trình học tại Viện SIGE không ạ? 😊 "
    "Chúng tôi luôn sẵn sàng hỗ trợ anh/chị!"
)

NUDGE_2_TEXT = (
    "Anh/chị ơi, Viện SIGE vẫn đang giữ suất học bổng ưu đãi cho mình nha! 🌟 "
    "Nếu cần tư vấn thêm, hãy nhắn tin cho chúng tôi bất cứ lúc nào ạ."
)


def _hours_since(dt_str: str) -> float:
    """
    Return how many hours have elapsed since the given UTC datetime string
    (SQLite stores datetimes as 'YYYY-MM-DD HH:MM:SS' in UTC by default).
    """
    try:
        dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        now = datetime.now(tz=timezone.utc)
        return (now - dt).total_seconds() / 3600
    except Exception as e:
        logger.error("[Nudge] Failed to parse datetime '%s': %s", dt_str, e)
        return 0.0


async def _run_nudge_check(send_fn) -> None:
    """
    Single check cycle: query all pending users and dispatch any due nudges.

    :param send_fn: callable(user_id: str, text: str) that sends a Zalo message.
                    Passed in to avoid circular imports with main.py.
    """
    pending = get_pending_nudge_users()
    if not pending:
        return

    logger.info("[Nudge] Checking %d pending user(s)…", len(pending))

    for row in pending:
        user_id = row["zalo_user_id"]
        last_msg = row["last_user_msg_at"]
        nudge1_sent = row["nudge1_sent"]
        nudge2_sent = row["nudge2_sent"]
        cancelled = row["cancelled"]

        # Safety guard (should already be filtered by DB query)
        if cancelled:
            continue

        hours_elapsed = _hours_since(last_msg)

        # ── Nudge 1 (12 h) ───────────────────────────────────────────────────
        if not nudge1_sent and hours_elapsed >= NUDGE_1_HOURS:
            logger.info(
                "[Nudge] Sending nudge 1 to user=%s (%.1f h elapsed)",
                user_id, hours_elapsed,
            )
            try:
                await asyncio.get_event_loop().run_in_executor(
                    None, send_fn, user_id, NUDGE_1_TEXT
                )
                mark_nudge_sent(user_id, 1)
            except Exception as e:
                logger.error("[Nudge] Failed to send nudge 1 to %s: %s", user_id, e)

        # ── Nudge 2 (24 h) ───────────────────────────────────────────────────
        if not nudge2_sent and hours_elapsed >= NUDGE_2_HOURS:
            logger.info(
                "[Nudge] Sending nudge 2 to user=%s (%.1f h elapsed)",
                user_id, hours_elapsed,
            )
            try:
                await asyncio.get_event_loop().run_in_executor(
                    None, send_fn, user_id, NUDGE_2_TEXT
                )
                mark_nudge_sent(user_id, 2)
            except Exception as e:
                logger.error("[Nudge] Failed to send nudge 2 to %s: %s", user_id, e)


async def nudge_scheduler_loop(send_fn) -> None:
    """
    Infinite async loop that wakes up every POLL_INTERVAL_SECONDS and runs
    the nudge check. Designed to be started as an asyncio background task
    from the FastAPI startup event.

    :param send_fn: callable(user_id: str, text: str) — the Zalo send function.
    """
    logger.info(
        "[Nudge] Scheduler started. Poll interval: %ds. Nudge windows: %dh / %dh.",
        POLL_INTERVAL_SECONDS, NUDGE_1_HOURS, NUDGE_2_HOURS,
    )
    while True:
        try:
            await _run_nudge_check(send_fn)
        except Exception as e:
            logger.error("[Nudge] Unexpected error in scheduler loop: %s", e)
        await asyncio.sleep(POLL_INTERVAL_SECONDS)
