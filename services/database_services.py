import sqlite3
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from config import DATABASE_PATH, TICKETS_TABLE_PATH

class DatabaseService:
    def __init__(self, db_path = DATABASE_PATH):
        self.db_path = db_path
        
        self._init_database()

    def _init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        with open(TICKETS_TABLE_PATH, "r") as sql_file:
            sql_script = sql_file.read()

        cursor.execute(sql_script)
        conn.commit()
        conn.close()

    def insert_tasks(self, assignee: str, action_item: str, 
                     blocker: Optional[str] = None, 
                     meeting_id: Optional[str] = None,
                     db_conn: sqlite3.Connection = None):
        try:
            own_conn = db_conn is None
            if own_conn:
                db_conn = sqlite3.connect(self.db_path)

            cursor = db_conn.cursor()
            cursor.execute("""
                INSERT INTO tasks (assignee_name, task_description, blocker_notes, meeting_id)
                VALUES (?, ?, ?, ?)""", 
                (assignee, action_item, blocker, meeting_id))
            
            task_id = cursor.lastrowid

        finally:
            if own_conn:
                db_conn.commit()
                db_conn.close()

    def insert_tasks_batch(self, tasks: List[dict], meeting_id: Optional[str] = None) -> List[int]:
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            task_ids = []

            for task in tasks:
                cursor.execute(
                    "INSERT INTO tasks (assignee_name, task_description, blocker_notes, meeting_id) VALUES (?, ?, ?, ?)",
                    (
                        task.get("assignee", ""),
                        task.get("action_items", ""),
                        task.get("blocker"),
                        meeting_id
                    )
                )
                task_ids.append(cursor.lastrowid)

            conn.commit()
            return task_ids
        finally:
            conn.close()

    def get_tasks_by_assignee(self, assignee_name: str) -> List[dict]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM tasks WHERE assignee_name = ? ORDER BY created_at DESC",
            (assignee_name,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_all_tasks(self) -> List[dict]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def update_task_status(self, task_id: int, status: str) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE tasks SET status = ? WHERE id = ?", (status, task_id))
        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return updated