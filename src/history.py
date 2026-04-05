import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "history.db")


def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _init_db():
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                url TEXT,
                verdict TEXT,
                avg_score REAL,
                scores TEXT,
                created_at TEXT
            )
        """)
        conn.commit()


_init_db()


def save_analysis(title: str, url: str, verdict: str, avg_score, scores: dict):
    with _get_conn() as conn:
        conn.execute(
            "INSERT INTO analyses (title, url, verdict, avg_score, scores, created_at) VALUES (?,?,?,?,?,?)",
            (title, url, verdict, avg_score, json.dumps(scores), datetime.now().strftime("%Y-%m-%d %H:%M")),
        )
        conn.commit()


def load_history(limit: int = 20) -> list[dict]:
    try:
        with _get_conn() as conn:
            rows = conn.execute(
                "SELECT id, title, url, verdict, avg_score, created_at as date FROM analyses ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]
    except Exception:
        return []


def delete_entry(entry_id: int):
    with _get_conn() as conn:
        conn.execute("DELETE FROM analyses WHERE id=?", (entry_id,))
        conn.commit()