from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


DB_PATH = Path(os.getenv("ECHO_DB_PATH", "logs/echo_app.db"))
_LOCK = threading.Lock()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _LOCK:
        conn = _ensure_conn()
        try:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS sessions (
                    token TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                );

                CREATE TABLE IF NOT EXISTS entries (
                    id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    mood TEXT,
                    response_text TEXT NOT NULL,
                    emotion_state_json TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                );

                CREATE TABLE IF NOT EXISTS drafts (
                    id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    mood TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                );

                CREATE TABLE IF NOT EXISTS reset_tokens (
                    token TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    used_at TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                );

                CREATE TABLE IF NOT EXISTS profiles (
                    user_id INTEGER PRIMARY KEY,
                    about TEXT DEFAULT '',
                    FOREIGN KEY(user_id) REFERENCES users(id)
                );

                CREATE INDEX IF NOT EXISTS idx_entries_user_created
                ON entries(user_id, created_at DESC);

                CREATE INDEX IF NOT EXISTS idx_drafts_user_created
                ON drafts(user_id, created_at DESC);

                CREATE INDEX IF NOT EXISTS idx_reset_user_created
                ON reset_tokens(user_id, created_at DESC);

                CREATE TABLE IF NOT EXISTS rate_limits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bucket_key TEXT NOT NULL,
                    created_at_epoch REAL NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_rate_limits_bucket_time
                ON rate_limits(bucket_key, created_at_epoch);
                """
            )
            conn.commit()
        finally:
            conn.close()


def get_profile(user_id: int) -> dict[str, Any]:
    conn = _ensure_conn()
    try:
        row = conn.execute("SELECT about FROM profiles WHERE user_id = ?", (user_id,)).fetchone()
        if row is None:
            return {"about": ""}
        return {"about": row["about"]}
    finally:
        conn.close()


def update_profile(user_id: int, about: str) -> None:
    with _LOCK:
        conn = _ensure_conn()
        try:
            conn.execute(
                """
                INSERT INTO profiles(user_id, about)
                VALUES(?, ?)
                ON CONFLICT(user_id) DO UPDATE SET about=excluded.about
                """,
                (user_id, about)
            )
            conn.commit()
        finally:
            conn.close()


def _hash_password(password: str, salt_hex: str) -> str:
    salt = bytes.fromhex(salt_hex)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
    return digest.hex()


def create_user(username: str, password: str) -> dict[str, Any]:
    salt_hex = secrets.token_hex(16)
    password_hash = _hash_password(password, salt_hex)
    with _LOCK:
        conn = _ensure_conn()
        try:
            cur = conn.execute(
                """
                INSERT INTO users(username, password_hash, salt, created_at)
                VALUES(?, ?, ?, ?)
                """,
                (username, password_hash, salt_hex, _utc_now()),
            )
            conn.commit()
            return {"id": cur.lastrowid, "username": username}
        finally:
            conn.close()


def authenticate_user(username: str, password: str) -> dict[str, Any] | None:
    conn = _ensure_conn()
    try:
        row = conn.execute(
            "SELECT id, username, password_hash, salt FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        if row is None:
            return None
        expected = row["password_hash"]
        actual = _hash_password(password, row["salt"])
        if not hmac.compare_digest(expected, actual):
            return None
        return {"id": row["id"], "username": row["username"]}
    finally:
        conn.close()


def create_session(user_id: int, days: int = 7) -> str:
    token = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=days)
    with _LOCK:
        conn = _ensure_conn()
        try:
            conn.execute(
                """
                INSERT INTO sessions(token, user_id, created_at, expires_at)
                VALUES(?, ?, ?, ?)
                """,
                (token, user_id, now.isoformat(), expires.isoformat()),
            )
            conn.commit()
            return token
        finally:
            conn.close()


def revoke_user_sessions(user_id: int) -> None:
    with _LOCK:
        conn = _ensure_conn()
        try:
            conn.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
            conn.commit()
        finally:
            conn.close()


def get_user_by_token(token: str) -> dict[str, Any] | None:
    now = datetime.now(timezone.utc).isoformat()
    conn = _ensure_conn()
    try:
        conn.execute("DELETE FROM sessions WHERE expires_at < ?", (now,))
        conn.commit()
        row = conn.execute(
            """
            SELECT u.id, u.username
            FROM sessions s
            JOIN users u ON u.id = s.user_id
            WHERE s.token = ? AND s.expires_at >= ?
            """,
            (token, now),
        ).fetchone()
        if row is None:
            return None
        return {"id": row["id"], "username": row["username"]}
    finally:
        conn.close()


def revoke_session(token: str) -> None:
    with _LOCK:
        conn = _ensure_conn()
        try:
            conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
            conn.commit()
        finally:
            conn.close()


def save_entry(
    *,
    entry_id: str,
    user_id: int,
    text: str,
    mood: str | None,
    response_text: str,
    emotion_state: dict[str, Any] | None,
) -> None:
    with _LOCK:
        conn = _ensure_conn()
        try:
            conn.execute(
                """
                INSERT INTO entries(id, user_id, text, mood, response_text, emotion_state_json, created_at)
                VALUES(?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry_id,
                    user_id,
                    text,
                    mood,
                    response_text,
                    json.dumps(emotion_state) if emotion_state is not None else None,
                    _utc_now(),
                ),
            )
            conn.commit()
        finally:
            conn.close()


def list_entries(user_id: int, limit: int = 100) -> list[dict[str, Any]]:
    conn = _ensure_conn()
    try:
        rows = conn.execute(
            """
            SELECT id, text, mood, response_text, emotion_state_json, created_at
            FROM entries
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
        return [
            {
                "id": row["id"],
                "text": row["text"],
                "mood": row["mood"],
                "responseText": row["response_text"],
                "emotionState": json.loads(row["emotion_state_json"]) if row["emotion_state_json"] else None,
                "createdAt": row["created_at"],
            }
            for row in rows
        ]
    finally:
        conn.close()


def save_draft(*, draft_id: str, user_id: int, text: str, mood: str | None) -> None:
    with _LOCK:
        conn = _ensure_conn()
        try:
            conn.execute(
                """
                INSERT INTO drafts(id, user_id, text, mood, created_at)
                VALUES(?, ?, ?, ?, ?)
                """,
                (draft_id, user_id, text, mood, _utc_now()),
            )
            conn.commit()
        finally:
            conn.close()


def list_drafts(user_id: int, limit: int = 100) -> list[dict[str, Any]]:
    conn = _ensure_conn()
    try:
        rows = conn.execute(
            """
            SELECT id, text, mood, created_at
            FROM drafts
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
        return [
            {
                "id": row["id"],
                "text": row["text"],
                "mood": row["mood"],
                "createdAt": row["created_at"],
            }
            for row in rows
        ]
    finally:
        conn.close()


def delete_draft(*, user_id: int, draft_id: str) -> bool:
    with _LOCK:
        conn = _ensure_conn()
        try:
            cur = conn.execute(
                "DELETE FROM drafts WHERE user_id = ? AND id = ?",
                (user_id, draft_id),
            )
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()


def update_entry(*, user_id: int, entry_id: str, text: str, mood: str | None) -> bool:
    with _LOCK:
        conn = _ensure_conn()
        try:
            cur = conn.execute(
                "UPDATE entries SET text = ?, mood = ? WHERE user_id = ? AND id = ?",
                (text, mood, user_id, entry_id),
            )
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()


def delete_entry(*, user_id: int, entry_id: str) -> bool:
    with _LOCK:
        conn = _ensure_conn()
        try:
            cur = conn.execute(
                "DELETE FROM entries WHERE user_id = ? AND id = ?",
                (user_id, entry_id),
            )
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()


def create_password_reset_token(username: str, minutes: int = 30) -> str | None:
    now = datetime.now(timezone.utc)
    expires = now + timedelta(minutes=minutes)
    token = secrets.token_urlsafe(24)
    with _LOCK:
        conn = _ensure_conn()
        try:
            user = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
            if user is None:
                return None
            conn.execute(
                """
                INSERT INTO reset_tokens(token, user_id, created_at, expires_at, used_at)
                VALUES(?, ?, ?, ?, NULL)
                """,
                (token, user["id"], now.isoformat(), expires.isoformat()),
            )
            conn.commit()
            return token
        finally:
            conn.close()


def consume_password_reset_token(token: str, new_password: str) -> bool:
    now = datetime.now(timezone.utc).isoformat()
    with _LOCK:
        conn = _ensure_conn()
        try:
            row = conn.execute(
                """
                SELECT rt.user_id
                FROM reset_tokens rt
                WHERE rt.token = ? AND rt.used_at IS NULL AND rt.expires_at >= ?
                """,
                (token, now),
            ).fetchone()
            if row is None:
                return False

            salt_hex = secrets.token_hex(16)
            password_hash = _hash_password(new_password, salt_hex)
            conn.execute(
                "UPDATE users SET password_hash = ?, salt = ? WHERE id = ?",
                (password_hash, salt_hex, row["user_id"]),
            )
            conn.execute(
                "UPDATE reset_tokens SET used_at = ? WHERE token = ?",
                (now, token),
            )
            conn.execute("DELETE FROM sessions WHERE user_id = ?", (row["user_id"],))
            conn.commit()
            return True
        finally:
            conn.close()


def consume_rate_limit(bucket_key: str, limit: int, window_seconds: int) -> bool:
    now = datetime.now(timezone.utc).timestamp()
    window_start = now - window_seconds
    with _LOCK:
        conn = _ensure_conn()
        try:
            conn.execute(
                "DELETE FROM rate_limits WHERE bucket_key = ? AND created_at_epoch < ?",
                (bucket_key, window_start),
            )
            count_row = conn.execute(
                "SELECT COUNT(1) AS c FROM rate_limits WHERE bucket_key = ?",
                (bucket_key,),
            ).fetchone()
            count = int(count_row["c"]) if count_row else 0
            if count >= limit:
                conn.commit()
                return False

            conn.execute(
                "INSERT INTO rate_limits(bucket_key, created_at_epoch) VALUES(?, ?)",
                (bucket_key, now),
            )
            conn.commit()
            return True
        finally:
            conn.close()
