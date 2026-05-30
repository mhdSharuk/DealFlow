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
        log.info("Initialising DealFlowOrchestrator")

        try:
            self.session_service = InMemorySessionService()
            self.db_service = DatabaseService()
            self.storage_service = StorageService()
        except Exception:
            log.error("Service initialisation failed:\n%s", traceback.format_exc())
            raise

        try:
            self.extractor_agent = create_extractor_agent()
            self.taskmage_agent = create_task_agent()
            self.hubspot_agent = create_hubspot_agent()
            self.email_agent = create_email_agent()
        except Exception:
            log.error("Agent loading failed:\n%s", traceback.format_exc())
            raise

        self.layer1_agent = ParallelAgent(
            name="layer1_parallel",
            sub_agents=[self.extractor_agent, self.taskmage_agent],
        )
        self.layer2_agent = ParallelAgent(
            name="layer2_parallel",
            sub_agents=[self.hubspot_agent, self.email_agent],
        )

        log.info("Orchestrator ready")

    async def process_transcript(self, raw_json: Dict[str, Any]) -> Dict[str, Any]:
        log.info("process_transcript started")

        try:
            parsed = TranscriptParser.parse_fireflies_json(raw_json)
        except Exception:
            log.error("Transcript parsing failed:\n%s", traceback.format_exc())
            raise

        transcript_text = parsed.get("transcript_text") or ""
        metadata = parsed.get("metadata") or {}
        meeting_id = metadata.get("meeting_id")

        if not transcript_text:
            raise ValueError(
                "Transcript text is empty after parsing. "
                "Check TranscriptParser.parse_fireflies_json()."
            )

        log.info(
            "Transcript parsed: meeting_id=%r, length=%d, internal_employees=%s",
            meeting_id,
            len(transcript_text),
            parsed.get("internal_employees", []),
        )

        layer1_results = await self._run_parallel_layer(
            parallel_agent=self.layer1_agent,
            user_message=self._build_layer1_context(parsed),
            output_keys={
                "extraction": self.extractor_agent.output_key,
                "tasks": self.taskmage_agent.output_key,
            },
            layer_label="Layer 1",
        )

        layer2_results = await self._run_parallel_layer(
            parallel_agent=self.layer2_agent,
            user_message=self._build_layer2_context(layer1_results),
            output_keys={
                "hubspot": self.hubspot_agent.output_key,
                "email": self.email_agent.output_key,
            },
            layer_label="Layer 2",
        )

        self._persist_outputs(layer2_results, meeting_id)

        return {
            "agent_1_extraction": layer1_results.get("extraction"),
            "agent_2_tickets": layer1_results.get("tasks"),
            "agent_3_hubspot": layer2_results.get("hubspot"),
            "agent_4_email": layer2_results.get("email"),
            "metadata": metadata,
        }

    async def _run_parallel_layer(
        self,
        parallel_agent: ParallelAgent,
        user_message: str,
        output_keys: Dict[str, str],
        layer_label: str,
    ) -> Dict[str, Any]:
        session_id = f"{parallel_agent.name}-{uuid.uuid4().hex}"

        await self.session_service.create_session(
            app_name=APP_NAME,
            user_id=SYSTEM_UID,
            session_id=session_id,
        )

        runner = Runner(
            agent=parallel_agent,
            app_name=APP_NAME,
            session_service=self.session_service,
        )

        try:
            async for event in runner.run_async(
                user_id=SYSTEM_UID,
                session_id=session_id,
                new_message=types.Content(
                    role="user",
                    parts=[types.Part(text=user_message)],
                ),
            ):
                if event.is_final_response():
                    log.debug(
                        "[%s] final response from %s",
                        layer_label,
                        getattr(event, "author", "unknown"),
                    )
        except Exception:
            log.error("[%s] runner failed:\n%s", layer_label, traceback.format_exc())
            raise

        session = await self.session_service.get_session(
            app_name=APP_NAME,
            user_id=SYSTEM_UID,
            session_id=session_id,
        )
        state = session.state if session else {}

        results: Dict[str, Any] = {}
        for logical_name, key in output_keys.items():
            raw_value = state.get(key)

            if raw_value is None:
                results[logical_name] = {"error": f"Agent output missing for key '{key}'"}
                continue

            parsed_value = raw_value if isinstance(raw_value, dict) else self._safe_parse(key, raw_value)
            results[logical_name] = parsed_value

        return results

    def _safe_parse(self, key: str, raw: Any) -> Any:
        if not isinstance(raw, str):
            return raw

        try:
            cleaned = raw.strip()

            if cleaned.startswith("```"):
                cleaned = cleaned[3:].strip()
                if cleaned.lower().startswith("json"):
                    cleaned = cleaned[4:].strip()
                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3].strip()

            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            log.error("JSON parse failed for %s: %s", key, exc)
            return {"error": "Failed to parse output", "raw": raw}

    def _build_layer1_context(self, parsed: Dict[str, Any]) -> str:
        employees = parsed.get("internal_employees") or []
        employee_list = ", ".join(employees) if employees else "Unknown"

        return f"""
Analyze the following sales call transcript.

INTERNAL EMPLOYEES (for task assignment only): {employee_list}

TRANSCRIPT:
{parsed.get('transcript_text', '')}

Return your analysis as JSON.
""".strip()

    def _build_layer2_context(self, layer1_results: Dict[str, Any]) -> str:
        extraction = json.dumps(layer1_results.get("extraction") or {}, indent=2)
        tasks = json.dumps(layer1_results.get("tasks") or {}, indent=2)

        return f"""
Generate CRM updates and a follow-up email based on the analysis below.

EXTRACTION RESULTS (topics, pain points, competitors):
{extraction}

TASK ASSIGNMENTS:
{tasks}

Return your output as JSON.
""".strip()

    def _persist_outputs(self, layer2_results: Dict[str, Any], meeting_id: Optional[str]) -> None:
        hubspot_data = layer2_results.get("hubspot") or {}
        if hubspot_data and not hubspot_data.get("error"):
            try:
                self.storage_service.save_hubspot_payload(hubspot_data, meeting_id)
            except Exception:
                log.error("save_hubspot_payload failed:\n%s", traceback.format_exc())

        email_data = layer2_results.get("email") or {}
        if not email_data or email_data.get("error"):
            return

        try:
            self.storage_service.save_email_draft(email_data, meeting_id)
        except Exception:
            log.error("save_email_draft failed:\n%s", traceback.format_exc())

        try:
            self.storage_service.save_mail_payload(email_data, meeting_id)
        except Exception:
            log.error("save_mail_payload failed:\n%s", traceback.format_exc())

    def save_tasks_to_database(
        self,
        tasks_output: Dict[str, Any],
        meeting_id: Optional[str] = None,
    ) -> None:
        tasks = tasks_output.get("tasks") or []

        if not tasks:
            return

        try:
            self.db_service.insert_tasks_batch(tasks, meeting_id)
        except Exception:
            log.error("insert_tasks_batch failed:\n%s", traceback.format_exc())