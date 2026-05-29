import json
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime

from config import OUTPUT_DIR

class StorageService:
    def __init__(self, output_dir: Path = OUTPUT_DIR):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def save_hubspot_payload(self, data: Dict[str, Any], meeting_id: Optional[str] = None) -> Path:
        filename = Path(f"hubspot_payload_{self._timestamp()}.json") if not meeting_id else Path(f"hubspot_{meeting_id}.json")
        filepath = self.output_dir / filename
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        return filepath

    def save_email_draft(self, data: Dict[str, Any], meeting_id: Optional[str] = None) -> Path:
        filename = Path(f"email_draft_{self._timestamp()}.txt") if not meeting_id else Path(f"email_{meeting_id}.txt")
        filepath = self.output_dir / filename
        with open(filepath, "w") as f:
            f.write(f"Subject: {data.get('email_subject', '')}\n\n")
            f.write(data.get("email_body", ""))
        return filepath

    def save_mail_payload(self, data: Dict[str, Any], meeting_id: Optional[str] = None) -> Path:
        filename = Path(f"mail_payload_{self._timestamp()}.json") if not meeting_id else Path(f"mail_{meeting_id}.json")
        filepath = self.output_dir / filename
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        return filepath

    def save_full_output(self, data: Dict[str, Any], meeting_id: Optional[str] = None) -> Path:
        filename = Path(f"full_output_{self._timestamp()}.json") if not meeting_id else Path(f"output_{meeting_id}.json")
        filepath = self.output_dir / filename
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        return filepath

    def _timestamp(self) -> str:
        return datetime.now().strftime("%Y%m%d_%H%M%S")