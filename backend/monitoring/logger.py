"""Request logging — every /api/chat, /api/csv-chat, /api/kpi call gets one
row: what endpoint, how long it took, which tools fired, whether it errored.

SQLite because this is a course project (single backend instance, no need for
a separate logging service). Swap DB_PATH for a real Postgres table if this
ever needs to survive across multiple instances.
"""

import os
import sqlite3
import time
from contextlib import contextmanager
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs.db")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS request_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    endpoint TEXT NOT NULL,
    lang TEXT,
    query_preview TEXT,
    tools_used TEXT,
    latency_ms REAL NOT NULL,
    status TEXT NOT NULL,
    error_message TEXT
);
"""


def _init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(_SCHEMA)


_init_db()


@contextmanager
def track_request(endpoint: str, lang: str | None = None, query: str | None = None):
    """Usage:

        with track_request("chat", lang, query) as ctx:
            answer, tools_used = run_chat_with_tools(...)
            ctx["tools_used"] = tools_used

    Logs latency + status automatically; exceptions are logged as errors and
    re-raised (this never swallows an error, it only records it).
    """
    start = time.perf_counter()
    ctx: dict = {"tools_used": []}
    try:
        yield ctx
    except Exception as exc:  # noqa: BLE001 — log then re-raise, don't swallow
        _write(endpoint, lang, query, ctx.get("tools_used", []), start, "error", str(exc))
        raise
    else:
        _write(endpoint, lang, query, ctx.get("tools_used", []), start, "ok", None)


def _write(endpoint, lang, query, tools_used, start, status, error_message):
    latency_ms = round((time.perf_counter() - start) * 1000, 1)
    query_preview = (query or "")[:200]
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO request_logs "
            "(created_at, endpoint, lang, query_preview, tools_used, latency_ms, status, error_message) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                datetime.now(timezone.utc).isoformat(),
                endpoint,
                lang,
                query_preview,
                ",".join(tools_used) if tools_used else None,
                latency_ms,
                status,
                error_message,
            ),
        )


def recent_logs(limit: int = 100) -> list[dict]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM request_logs ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


def summary_stats() -> dict:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        total = conn.execute("SELECT COUNT(*) AS n FROM request_logs").fetchone()["n"]
        errors = conn.execute(
            "SELECT COUNT(*) AS n FROM request_logs WHERE status = 'error'"
        ).fetchone()["n"]
        avg_latency = conn.execute(
            "SELECT AVG(latency_ms) AS avg_ms FROM request_logs"
        ).fetchone()["avg_ms"]
        by_endpoint = conn.execute(
            "SELECT endpoint, COUNT(*) AS n, AVG(latency_ms) AS avg_ms "
            "FROM request_logs GROUP BY endpoint"
        ).fetchall()
        by_tool = conn.execute(
            "SELECT tools_used, COUNT(*) AS n FROM request_logs "
            "WHERE tools_used IS NOT NULL GROUP BY tools_used"
        ).fetchall()

    return {
        "total_requests": total,
        "error_count": errors,
        "error_rate_pct": round(errors / total * 100, 1) if total else 0,
        "avg_latency_ms": round(avg_latency, 1) if avg_latency else 0,
        "by_endpoint": [dict(r) for r in by_endpoint],
        "by_tools_used": [dict(r) for r in by_tool],
    }
