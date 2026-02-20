import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager
import os

DB_PATH = Path(os.getenv("WEBGEN_DATA_DIR", "/workspace/data")) / "jobs.db"


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                domain TEXT DEFAULT 'pending',
                status TEXT DEFAULT 'pending',
                created_at TEXT,
                updated_at TEXT,
                snapshot_tokens INTEGER,
                strategy TEXT,
                error TEXT,
                zip_path TEXT
            )
        """)


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def create_job(snapshot_tokens: int = 0) -> str:
    job_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO jobs (id, status, created_at, updated_at, snapshot_tokens) VALUES (?,?,?,?,?)",
            (job_id, "pending", now, now, snapshot_tokens),
        )
    return job_id


def update_job(job_id: str, **kwargs):
    kwargs["updated_at"] = datetime.utcnow().isoformat()
    sets = ", ".join(f"{k}=?" for k in kwargs)
    vals = list(kwargs.values()) + [job_id]
    with get_conn() as conn:
        conn.execute(f"UPDATE jobs SET {sets} WHERE id=?", vals)


def get_job(job_id: str):
    with get_conn() as conn:
        return conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()


def get_all_jobs():
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM jobs ORDER BY created_at DESC"
        ).fetchall()


def delete_job(job_id: str):
    with get_conn() as conn:
        conn.execute("DELETE FROM jobs WHERE id=?", (job_id,))
