"""SQLite persistence for chatbot sessions and chat messages."""

import json
import os
import sqlite3
import threading
import time
import uuid
from typing import Any, Dict, List, Optional

from retrieval_pipeline.config import CHAT_DB_PATH, CHAT_SESSION_TTL_SEC

_db_lock = threading.Lock()


def _connect() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(CHAT_DB_PATH), exist_ok=True)
    conn = sqlite3.connect(CHAT_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initialize SQLite schema for chat sessions and messages."""
    with _db_lock:
        conn = _connect()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    session_id TEXT PRIMARY KEY,
                    file_name TEXT,
                    analyses_json TEXT NOT NULL,
                    summary_text TEXT,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    confidence REAL,
                    fallback_used INTEGER DEFAULT 0,
                    citations_json TEXT,
                    created_at REAL NOT NULL,
                    FOREIGN KEY(session_id) REFERENCES chat_sessions(session_id)
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_chat_messages_session ON chat_messages(session_id)")
            conn.commit()
        finally:
            conn.close()


def cleanup_expired_sessions(ttl_sec: Optional[int] = None) -> int:
    """Delete expired sessions and associated messages."""
    ttl = ttl_sec or CHAT_SESSION_TTL_SEC
    cutoff = time.time() - ttl

    with _db_lock:
        conn = _connect()
        try:
            rows = conn.execute(
                "SELECT session_id FROM chat_sessions WHERE updated_at < ?",
                (cutoff,),
            ).fetchall()
            session_ids = [r["session_id"] for r in rows]
            if not session_ids:
                return 0

            conn.executemany(
                "DELETE FROM chat_messages WHERE session_id = ?",
                [(sid,) for sid in session_ids],
            )
            conn.executemany(
                "DELETE FROM chat_sessions WHERE session_id = ?",
                [(sid,) for sid in session_ids],
            )
            conn.commit()
            return len(session_ids)
        finally:
            conn.close()


def create_session(file_name: str, analyses: List[Dict[str, Any]], summary: str) -> str:
    """Create a new chat session and persist contract context."""
    session_id = str(uuid.uuid4())
    now = time.time()

    with _db_lock:
        conn = _connect()
        try:
            conn.execute(
                """
                INSERT INTO chat_sessions(session_id, file_name, analyses_json, summary_text, created_at, updated_at)
                VALUES(?, ?, ?, ?, ?, ?)
                """,
                (session_id, file_name, json.dumps(analyses), summary, now, now),
            )
            conn.commit()
        finally:
            conn.close()

    return session_id


def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Fetch a session and deserialize contract context."""
    with _db_lock:
        conn = _connect()
        try:
            row = conn.execute(
                "SELECT * FROM chat_sessions WHERE session_id = ?",
                (session_id,),
            ).fetchone()
            if not row:
                return None

            return {
                "session_id": row["session_id"],
                "file_name": row["file_name"],
                "analyses": json.loads(row["analyses_json"]),
                "summary": row["summary_text"] or "",
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
        finally:
            conn.close()


def touch_session(session_id: str) -> None:
    """Update session timestamp to keep it active."""
    with _db_lock:
        conn = _connect()
        try:
            conn.execute(
                "UPDATE chat_sessions SET updated_at = ? WHERE session_id = ?",
                (time.time(), session_id),
            )
            conn.commit()
        finally:
            conn.close()


def add_message(
    session_id: str,
    role: str,
    content: str,
    confidence: Optional[float] = None,
    fallback_used: bool = False,
    citations: Optional[List[Dict[str, Any]]] = None,
) -> None:
    """Persist a chat message for a session."""
    with _db_lock:
        conn = _connect()
        try:
            conn.execute(
                """
                INSERT INTO chat_messages(session_id, role, content, confidence, fallback_used, citations_json, created_at)
                VALUES(?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    role,
                    content,
                    confidence,
                    1 if fallback_used else 0,
                    json.dumps(citations or []),
                    time.time(),
                ),
            )
            conn.execute(
                "UPDATE chat_sessions SET updated_at = ? WHERE session_id = ?",
                (time.time(), session_id),
            )
            conn.commit()
        finally:
            conn.close()


def get_messages(session_id: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Fetch recent chat history in chronological order."""
    with _db_lock:
        conn = _connect()
        try:
            rows = conn.execute(
                """
                SELECT * FROM chat_messages
                WHERE session_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (session_id, limit),
            ).fetchall()
        finally:
            conn.close()

    history: List[Dict[str, Any]] = []
    for row in reversed(rows):
        history.append(
            {
                "role": row["role"],
                "content": row["content"],
                "confidence": row["confidence"],
                "fallback_used": bool(row["fallback_used"]),
                "citations": json.loads(row["citations_json"] or "[]"),
                "created_at": row["created_at"],
            }
        )
    return history


def is_db_ready() -> bool:
    """Simple readiness probe for health endpoint."""
    try:
        init_db()
        return True
    except Exception:
        return False
