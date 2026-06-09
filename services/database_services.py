from typing import List, Optional

from core.config import get_supabase_client, SUPABASE_TASKS_TABLE

class DatabaseService:
    def __init__(self):
        self.db = get_supabase_client()

    def insert_tasks_batch(self, tasks: List[dict], meeting_id: Optional[str] = None) -> None:
        rows = [
            {
                "assignee_name": task.get("assignee", ""),
                "task_description": task.get("action_items", ""),
                "blocker_notes": task.get("blocker"),
                "meeting_id": meeting_id,
            }
            for task in tasks
        ]
        self.db.table(SUPABASE_TASKS_TABLE).insert(rows).execute()

    def get_tasks_by_assignee(self, assignee_name: str) -> List[dict]:
        res = self.db.table(SUPABASE_TASKS_TABLE).select("*").eq("assignee_name", assignee_name).order("created_at", desc=True).execute()
        return res.data or []

    def get_all_tasks(self) -> List[dict]:
        res = self.db.table(SUPABASE_TASKS_TABLE).select("*").order("created_at", desc=True).execute()
        return res.data or []

    def update_task_status(self, task_id: int, status: str) -> bool:
        res = self.db.table(SUPABASE_TASKS_TABLE).update({"status": status}).eq("id", task_id).execute()
        return bool(res.data)
