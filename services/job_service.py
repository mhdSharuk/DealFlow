import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import DATABASE_PATH, JOBS_TABLE_PATH


def _utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.row_factory = sqlite3.Row
    return conn


class JobService:
    def __init__(self, db_path: Path = DATABASE_PATH):
        self.db_path = db_path
        self._init_table()

    def _init_table(self) -> None:
        conn = _connect(self.db_path)
        with open(JOBS_TABLE_PATH, "r") as f:
            conn.executescript(f.read())
        conn.close()

    def create_job(self, raw_payload: Dict[str, Any], source_file: str = "") -> str:
        job_id = uuid.uuid4().hex
        conn = _connect(self.db_path)
        try:
            conn.execute(
                """INSERT INTO jobs (id, status, raw_payload, source_file, created_at)
                   VALUES (?, 'pending', ?, ?, ?)""",
                (job_id, json.dumps(raw_payload), source_file, _utcnow()),
            )
            conn.commit()
        finally:
            conn.close()
        return job_id

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        conn = _connect(self.db_path)
        try:
            row = conn.execute(
                "SELECT * FROM jobs WHERE id = ?", (job_id,)
            ).fetchone()
            return self._deserialise(dict(row)) if row else None
        finally:
            conn.close()

    def get_all_jobs(self) -> List[Dict[str, Any]]:
        conn = _connect(self.db_path)
        try:
            rows = conn.execute(
                """SELECT id, meeting_id, source_file, status,
                          created_at, started_at, completed_at
                   FROM jobs ORDER BY created_at DESC"""
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def update_job_status(
        self,
        job_id: str,
        status: str,
        result: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        meeting_id: Optional[str] = None,
    ) -> None:
        now = _utcnow()
        conn = _connect(self.db_path)
        try:
            if status == "processing":
                conn.execute(
                    "UPDATE jobs SET status=?, started_at=? WHERE id=?",
                    (status, now, job_id),
                )
            elif status in ("complete", "failed"):
                conn.execute(
                    """UPDATE jobs
                       SET status=?, completed_at=?, result=?,
                           error_message=?, meeting_id=?
                       WHERE id=?""",
                    (
                        status, now,
                        json.dumps(result) if result is not None else None,
                        error_message,
                        meeting_id,
                        job_id,
                    ),
                )
            else:
                conn.execute(
                    "UPDATE jobs SET status=? WHERE id=?", (status, job_id)
                )
            conn.commit()
        finally:
            conn.close()

    def job_exists_for_file(self, source_file: str) -> bool:
        """Return True if a job has already been created for this filename."""
        conn = _connect(self.db_path)
        try:
            row = conn.execute(
                "SELECT id FROM jobs WHERE source_file = ? LIMIT 1", (source_file,)
            ).fetchone()
            return row is not None
        finally:
            conn.close()

    @staticmethod
    def _deserialise(row: Dict[str, Any]) -> Dict[str, Any]:
        for col in ("raw_payload", "result"):
            if isinstance(row.get(col), str):
                try:
                    row[col] = json.loads(row[col])
                except json.JSONDecodeError:
                    pass
        return row
