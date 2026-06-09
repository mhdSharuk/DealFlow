import json
from typing import Any, Dict, Optional

from core.config import get_supabase_client, SUPABASE_BUCKET

class StorageService:
    def __init__(self):
        self.db = get_supabase_client()

    def save_hubspot_payload(self, data: Dict[str, Any], meeting_id: Optional[str] = None) -> str:
        filename = f"hubspot_{meeting_id}.json" if meeting_id else f"hubspot_payload.json"
        self.db.storage.from_(SUPABASE_BUCKET).upload(filename, json.dumps(data).encode(), {"content-type": "application/json"})
        return filename

    def save_email_draft(self, data: Dict[str, Any], meeting_id: Optional[str] = None) -> str:
        filename = f"email_{meeting_id}.txt" if meeting_id else "email_draft.txt"
        body = f"Subject: {data.get('email_subject', '')}\n\n{data.get('email_body', '')}"
        self.db.storage.from_(SUPABASE_BUCKET).upload(filename, body.encode(), {"content-type": "text/plain"})
        return filename

    def save_mail_payload(self, data: Dict[str, Any], meeting_id: Optional[str] = None) -> str:
        filename = f"mail_{meeting_id}.json" if meeting_id else "mail_payload.json"
        self.db.storage.from_(SUPABASE_BUCKET).upload(filename, json.dumps(data).encode(), {"content-type": "application/json"})
        return filename

    def save_full_output(self, data: Dict[str, Any], meeting_id: Optional[str] = None) -> str:
        filename = f"output_{meeting_id}.json" if meeting_id else "full_output.json"
        self.db.storage.from_(SUPABASE_BUCKET).upload(filename, json.dumps(data).encode(), {"content-type": "application/json"})
        return filename
