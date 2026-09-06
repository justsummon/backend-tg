"""
Простое хранилище на SQLite — достаточно для прототипа хакатона.
Храним профили и результаты анализа, чтобы:
- бот и WebApp могли обращаться к одному и тому же результату по id;
- можно было вернуться к своему roadmap позже, не проходя диагностику снова.
"""
import json
import sqlite3
import uuid
from contextlib import contextmanager

DB_PATH = "career_navigator.db"


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS profiles (
                id TEXT PRIMARY KEY,
                telegram_id INTEGER,
                profile_json TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS results (
                id TEXT PRIMARY KEY,
                profile_id TEXT NOT NULL,
                result_json TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (profile_id) REFERENCES profiles (id)
            )
        """)
        conn.commit()


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()


def save_profile(telegram_id: int | None, profile_dict: dict) -> str:
    profile_id = str(uuid.uuid4())
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO profiles (id, telegram_id, profile_json) VALUES (?, ?, ?)",
            (profile_id, telegram_id, json.dumps(profile_dict, ensure_ascii=False)),
        )
        conn.commit()
    return profile_id


def save_result(profile_id: str, result_dict: dict) -> str:
    result_id = str(uuid.uuid4())
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO results (id, profile_id, result_json) VALUES (?, ?, ?)",
            (result_id, profile_id, json.dumps(result_dict, ensure_ascii=False)),
        )
        conn.commit()
    return result_id


def get_result(result_id: str) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT result_json FROM results WHERE id = ?", (result_id,)
        ).fetchone()
    return json.loads(row[0]) if row else None


def get_latest_result_for_telegram_id(telegram_id: int) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT r.result_json FROM results r
            JOIN profiles p ON r.profile_id = p.id
            WHERE p.telegram_id = ?
            ORDER BY r.created_at DESC LIMIT 1
            """,
            (telegram_id,),
        ).fetchone()
    return json.loads(row[0]) if row else None
