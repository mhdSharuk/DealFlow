import json
import logging
import traceback
import uuid
from typing import Any, Dict, Optional

from google.adk.agents import ParallelAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from agents.crm_agent.agent import create_hubspot_agent
from agents.email_agent.agent import create_email_agent
from agents.extractor_agent.agent import create_extractor_agent
from agents.task_agent.agent import create_task_agent
from services.database_services import DatabaseService
from services.storage_services import StorageService
from utils.transcript_parser import TranscriptParser

log = logging.getLogger("sales_copilot")

APP_NAME = "sales_copilot"
SYSTEM_UID = "system"


class DealFlowOrchestrator:
    def __init__(self):
        self.session_service = InMemorySessionService()
        self.db_service = DatabaseService()
        self.storage_service = StorageService()

        self.extractor_agent = create_extractor_agent()
        self.taskmage_agent = create_task_agent()
        self.hubspot_agent = create_hubspot_agent()
        self.email_agent = create_email_agent()

        self.layer1_agent = ParallelAgent(
            name="layer1_parallel",
            sub_agents=[self.extractor_agent, self.taskmage_agent],
        )
        self.layer2_agent = ParallelAgent(
            name="layer2_parallel",
            sub_agents=[self.hubspot_agent, self.email_agent],
        )

    async def process_transcript(self, raw_json: Dict[str, Any]) -> Dict[str, Any]:
        parsed = TranscriptParser.parse_fireflies_json(raw_json)
        transcript_text = parsed.get("transcript_text") or ""
        metadata = parsed.get("metadata") or {}
        meeting_id = metadata.get("meeting_id")

        if not transcript_text:
            raise ValueError("Transcript text is empty after parsing.")

        log.info("Transcript parsed: meeting_id=%r, length=%d", meeting_id, len(transcript_text))

        layer1_results = await self._run_parallel_layer(
            agent=self.layer1_agent,
            message=self._build_layer1_context(parsed),
            output_keys={
                "extraction": self.extractor_agent.output_key,
                "tasks": self.taskmage_agent.output_key,
            },
        )

        layer2_results = await self._run_parallel_layer(
            agent=self.layer2_agent,
            message=self._build_layer2_context(layer1_results),
            output_keys={
                "hubspot": self.hubspot_agent.output_key,
                "email": self.email_agent.output_key,
            },
        )

        self._persist_outputs(layer2_results, meeting_id)
        self.save_tasks_to_database(layer1_results.get("tasks"), meeting_id)

        return {
            "agent_1_extraction": layer1_results.get("extraction"),
            "agent_2_tickets": layer1_results.get("tasks"),
            "agent_3_hubspot": layer2_results.get("hubspot"),
            "agent_4_email": layer2_results.get("email"),
            "metadata": metadata,
        }

    async def _run_parallel_layer(
        self, agent: ParallelAgent, message: str, output_keys: Dict[str, str]
    ) -> Dict[str, Any]:
        session_id = f"{agent.name}-{uuid.uuid4().hex}"

        await self.session_service.create_session(
            app_name=APP_NAME, user_id=SYSTEM_UID, session_id=session_id
        )

        runner = Runner(agent=agent, app_name=APP_NAME, session_service=self.session_service)

        async for _ in runner.run_async(
            user_id=SYSTEM_UID,
            session_id=session_id,
            new_message=types.Content(role="user", parts=[types.Part(text=message)]),
        ):
            pass

        session = await self.session_service.get_session(
            app_name=APP_NAME, user_id=SYSTEM_UID, session_id=session_id
        )
        state = session.state if session else {}

        return {name: self._parse_output(state.get(key)) for name, key in output_keys.items()}

    def _parse_output(self, raw: Any) -> Any:
        if raw is None:
            return {"error": "Agent output missing"}
        if isinstance(raw, dict):
            return raw
        try:
            text = raw.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[-1]   # drop opening fence line
            if text.endswith("```"):
                text = text.rsplit("\n", 1)[0]   # drop closing fence line
            return json.loads(text.strip())
        except (json.JSONDecodeError, AttributeError):
            return {"error": "Failed to parse output", "raw": raw}

    def _build_layer1_context(self, parsed: Dict[str, Any]) -> str:
        employees = ", ".join(parsed.get("internal_employees") or []) or "Unknown"
        return (
            f"Analyze the following sales call transcript.\n\n"
            f"INTERNAL EMPLOYEES (for task assignment only): {employees}\n\n"
            f"TRANSCRIPT:\n{parsed.get('transcript_text', '')}\n\n"
            f"Return your analysis as JSON."
        )

    def _build_layer2_context(self, layer1_results: Dict[str, Any]) -> str:
        extraction = json.dumps(layer1_results.get("extraction") or {}, indent=2)
        tasks = json.dumps(layer1_results.get("tasks") or {}, indent=2)
        return (
            f"Generate CRM updates and a follow-up email based on the analysis below.\n\n"
            f"EXTRACTION RESULTS (topics, pain points, competitors):\n{extraction}\n\n"
            f"TASK ASSIGNMENTS:\n{tasks}\n\n"
            f"Return your output as JSON."
        )

    def _persist_outputs(self, layer2_results: Dict[str, Any], meeting_id: Optional[str]) -> None:
        hubspot_data = layer2_results.get("hubspot") or {}
        if hubspot_data and not hubspot_data.get("error"):
            try:
                self.storage_service.save_hubspot_payload(hubspot_data, meeting_id)
            except Exception:
                log.error("save_hubspot_payload failed:\n%s", traceback.format_exc())

        email_data = layer2_results.get("email") or {}
        if email_data and not email_data.get("error"):
            try:
                self.storage_service.save_email_draft(email_data, meeting_id)
                self.storage_service.save_mail_payload(email_data, meeting_id)
            except Exception:
                log.error("save_email failed:\n%s", traceback.format_exc())

    def save_tasks_to_database(
        self, tasks_output: Dict[str, Any], meeting_id: Optional[str] = None
    ) -> None:
        tasks = (tasks_output or {}).get("tasks") or []
        if not tasks:
            return
        try:
            self.db_service.insert_tasks_batch(tasks, meeting_id)
        except Exception:
            log.error("insert_tasks_batch failed:\n%s", traceback.format_exc())
