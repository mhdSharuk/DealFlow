import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from core.config import get_supabase_client


def _utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class JobService:
    def __init__(self):
        self.db = get_supabase_client()

    def create_job(self, raw_payload: Dict[str, Any], source_file: str = "") -> str:
        job_id = uuid.uuid4().hex
        self.db.table("jobs").insert({
            "id": job_id,
            "status": "pending",
            "raw_payload": json.dumps(raw_payload),
            "source_file": source_file,
            "created_at": _utcnow(),
        }).execute()
        return job_id
    
    def create_dead_job(self, source_file: str, error_message: str) -> None:
        job_id = uuid.uuid4().hex
        self.db.table("jobs").insert({
            "id": job_id,
            "status": "dead",
            "raw_payload": None,
            "source_file": source_file,
            "error_message": f"{error_message}",
            "created_at": _utcnow(),
        }).execute()

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        res = self.db.table("jobs").select("*").eq("id", job_id).single().execute()
        return self._deserialise(res.data) if res.data else None

    def get_all_jobs(self) -> List[Dict[str, Any]]:
        res = self.db.table("jobs").select(
            "id, meeting_id, source_file, status, created_at, started_at, completed_at"
        ).order("created_at", desc=True).execute()
        return res.data or []

    def update_job_status(
        self,
        job_id: str,
        status: str,
        result: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        meeting_id: Optional[str] = None,
    ) -> None:
        now = _utcnow()
        if status == "processing":
            payload = {"status": status, "started_at": now}
        elif status in ("complete", "failed"):
            payload = {
                "status": status,
                "completed_at": now,
                "result": json.dumps(result) if result is not None else None,
                "error_message": error_message,
                "meeting_id": meeting_id,
            }
        else:
            payload = {"status": status, "error_message": error_message}

        self.db.table("jobs").update(payload).eq("id", job_id).execute()

    def get_jobs_by_status(self, status: str) -> List[Dict[str, Any]]:
        res = self.db.table("jobs").select(
            "id, meeting_id, source_file, status, created_at, started_at, completed_at, error_message"
        ).eq("status", status).order("created_at", desc=True).execute()
        return res.data or []

    def job_exists_for_file(self, source_file: str) -> bool:
        res = self.db.table("jobs").select("id").eq("source_file", source_file).in_("status", ["pending", "processing"]).limit(1).execute()
        return bool(res.data)

    @staticmethod
    def _deserialise(row: Dict[str, Any]) -> Dict[str, Any]:
        for col in ("raw_payload", "result"):
            if isinstance(row.get(col), str):
                try:
                    row[col] = json.loads(row[col])
                except json.JSONDecodeError:
                    pass
        return row
