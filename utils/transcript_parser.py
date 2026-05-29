import json
from typing import Dict, Any, List, Optional

class TranscriptParser:
    def parse_fireflies_json(raw_json: Dict[str, Any]) -> Dict[str, Any]:
        meeting_metadata = {
            'meeting_id'       : raw_json.get('meeting_id', ""),
            'title'            : raw_json.get('title', ""), 
            'recording_at'     : raw_json.get('recording_at', ""),
            'duration_minutes' : raw_json.get('duration_minutes', 0),
            'call_type'        : raw_json.get('call_type', ""),
            'customer_company' : raw_json.get('customer_company', ""),
        }

        internal_attendees = []
        customer_attendees = []

        for attendee in raw_json.get("redwood_attendees", []):
            if isinstance(attendee, str):
                internal_attendees.append(attendee.split(" (")[0] if " (" in attendee else attendee)
            elif isinstance(attendee, dict):
                internal_attendees.append(attendee.get("name", attendee.get("email", "")))

        for attendee in raw_json.get("customer_attendees", []):
            if isinstance(attendee, str):
                customer_attendees.append(attendee.split(" (")[0] if " (" in attendee else attendee)
            elif isinstance(attendee, dict):
                customer_attendees.append(attendee.get("name", attendee.get("email", "")))


        transcript_body = raw_json.get("transcript")
        split_point = 'Transcript\n' if 'Transcript\n' in transcript_body else 'Transcript body:'
        transcript_body = transcript_body.split(split_point)[-1].strip() if transcript_body else ""

        return {
            "metadata": meeting_metadata,
            "transcript_text": transcript_body,
            "internal_employees": internal_attendees,
            "customer_attendees": customer_attendees,
            "raw_data": raw_json
        }
        