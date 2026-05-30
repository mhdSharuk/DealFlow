import asyncio
import json
import logging
import traceback
from typing import Any, Dict, Optional

from google.genai import types
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

from agents.extractor_agent.agent import create_extractor_agent
from agents.task_agent.agent import create_task_agent
from agents.crm_agent.agent import create_hubspot_agent
from agents.email_agent.agent import create_email_agent

from services.database_services import DatabaseService
from services.storage_services import StorageService
from utils.transcript_parser import TranscriptParser

# ─────────────────────────────────────────────────────────────────────────────
#  Logger — terminal gets full tracebacks; UI handler (attached in ui.py)
#  gets clean messages only.
# ─────────────────────────────────────────────────────────────────────────────
log = logging.getLogger("sales_copilot")


class DealFlowOrchestrator:
    def __init__(self):
        log.info("Initialising DealFlowOrchestrator…")
        try:
            self.session_service = InMemorySessionService()
            self.db_service      = DatabaseService()
            self.storage_service = StorageService()
            log.info("Services initialised: InMemorySession · Database · Storage")
        except Exception:
            log.error("Failed to initialise services:\n" + traceback.format_exc())
            raise

        try:
            self.extractor_agent = create_extractor_agent()
            self.taskmage_agent  = create_task_agent()
            self.hubspot_agent   = create_hubspot_agent()
            self.email_agent     = create_email_agent()
            log.info("Agents loaded: Extractor · Taskmage · HubSpot · Email")
        except Exception:
            log.error("Failed to load agents:\n" + traceback.format_exc())
            raise

    # ─────────────────────────────────────────────────────────────────────────
    #  Public entry point
    # ─────────────────────────────────────────────────────────────────────────
    async def process_transcript(self, raw_json: Dict[str, Any]) -> Dict[str, Any]:
        log.info("─" * 55)
        log.info("process_transcript() called")

        # ── 1. Parse ──────────────────────────────────────────────────────────
        log.info("Parsing Fireflies JSON via TranscriptParser…")
        try:
            parsed = TranscriptParser.parse_fireflies_json(raw_json)
        except Exception:
            log.error("TranscriptParser.parse_fireflies_json() raised:\n" + traceback.format_exc())
            raise

        # Validate required fields so downstream never receives None
        transcript_text = parsed.get("transcript_text") or ""
        metadata        = parsed.get("metadata") or {}
        meeting_id      = metadata.get("meeting_id")  # allowed to be None

        if not transcript_text:
            log.error(
                "TranscriptParser returned an empty transcript_text. "
                f"Keys present in parsed output: {list(parsed.keys())}"
            )
            raise ValueError(
                "Transcript text is empty after parsing. "
                "Check TranscriptParser.parse_fireflies_json() — it may not recognise this JSON schema."
            )

        log.info(f"Transcript parsed OK — meeting_id={meeting_id!r}  "
                 f"transcript_length={len(transcript_text)} chars  "
                 f"internal_employees={parsed.get('internal_employees', [])}")

        # ── 2. Layer 1 ────────────────────────────────────────────────────────
        log.info("Starting Layer 1 (parallel): Extractor + Taskmage")
        try:
            layer1_outputs = await self._execute_layer1_parallel(parsed)
        except Exception:
            log.error("Layer 1 failed:\n" + traceback.format_exc())
            raise
        log.info("Layer 1 complete")

        # ── 3. Layer 2 ────────────────────────────────────────────────────────
        log.info("Starting Layer 2 (parallel): HubSpot + Email")
        try:
            layer2_outputs = await self._execute_layer2_parallel(layer1_outputs)
        except Exception:
            log.error("Layer 2 failed:\n" + traceback.format_exc())
            raise
        log.info("Layer 2 complete")

        # ── 4. Persist ────────────────────────────────────────────────────────
        log.info(f"Persisting outputs — meeting_id={meeting_id!r}")
        try:
            self._persist_outputs(layer2_outputs, meeting_id)
        except Exception:
            # Non-fatal — log and continue so UI still gets results
            log.error("_persist_outputs() raised (non-fatal):\n" + traceback.format_exc())

        full_output = {
            "agent_1_extraction": layer1_outputs.get("extraction"),
            "agent_2_tickets":    layer1_outputs.get("tasks"),
            "agent_3_hubspot":    layer2_outputs.get("hubspot"),
            "agent_4_email":      layer2_outputs.get("email"),
            "metadata":           metadata,
        }

        log.info("process_transcript() finished — returning full output")
        log.info("─" * 55)
        return full_output

    # ─────────────────────────────────────────────────────────────────────────
    #  Layer execution
    # ─────────────────────────────────────────────────────────────────────────
    async def _execute_layer1_parallel(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        extraction_context = self._build_extraction_context(parsed_data)
        tasks_context      = self._build_tasks_context(parsed_data)

        log.debug(f"Extractor context length : {len(extraction_context)} chars")
        log.debug(f"Taskmage context length  : {len(tasks_context)} chars")

        extraction_task = self._run_agent(self.extractor_agent, extraction_context, "extraction_session")
        tasks_task      = self._run_agent(self.taskmage_agent,  tasks_context,      "tasks_session")

        results = await asyncio.gather(extraction_task, tasks_task, return_exceptions=True)

        extraction_raw, tasks_raw = results

        if isinstance(extraction_raw, Exception):
            log.error("Extractor agent raised:\n" + "".join(traceback.format_exception(type(extraction_raw), extraction_raw, extraction_raw.__traceback__)))
            extraction_result = {"error": "Extractor agent failed", "detail": str(extraction_raw)}
        else:
            log.info(f"Extractor raw response length: {len(extraction_raw)} chars")
            extraction_result = self._parse_agent_output("extractor", extraction_raw)

        if isinstance(tasks_raw, Exception):
            log.error("Taskmage agent raised:\n" + "".join(traceback.format_exception(type(tasks_raw), tasks_raw, tasks_raw.__traceback__)))
            tasks_result = {"error": "Taskmage agent failed", "detail": str(tasks_raw)}
        else:
            log.info(f"Taskmage raw response length: {len(tasks_raw)} chars")
            tasks_result = self._parse_agent_output("taskmage", tasks_raw)

        return {"extraction": extraction_result, "tasks": tasks_result}

    async def _execute_layer2_parallel(self, layer1_outputs: Dict[str, Any]) -> Dict[str, Any]:
        hubspot_context = self._build_hubspot_context(layer1_outputs)
        email_context   = self._build_email_context(layer1_outputs)

        log.debug(f"HubSpot context length: {len(hubspot_context)} chars")
        log.debug(f"Email context length  : {len(email_context)} chars")

        hubspot_task = self._run_agent(self.hubspot_agent, hubspot_context, "hubspot_session")
        email_task   = self._run_agent(self.email_agent,   email_context,   "email_session")

        results = await asyncio.gather(hubspot_task, email_task, return_exceptions=True)

        hubspot_raw, email_raw = results

        if isinstance(hubspot_raw, Exception):
            log.error("HubSpot agent raised:\n" + "".join(traceback.format_exception(type(hubspot_raw), hubspot_raw, hubspot_raw.__traceback__)))
            hubspot_result = {"error": "HubSpot agent failed", "detail": str(hubspot_raw)}
        else:
            log.info(f"HubSpot raw response length: {len(hubspot_raw)} chars")
            hubspot_result = self._parse_agent_output("hubspot", hubspot_raw)

        if isinstance(email_raw, Exception):
            log.error("Email agent raised:\n" + "".join(traceback.format_exception(type(email_raw), email_raw, email_raw.__traceback__)))
            email_result = {"error": "Email agent failed", "detail": str(email_raw)}
        else:
            log.info(f"Email raw response length: {len(email_raw)} chars")
            email_result = self._parse_agent_output("email", email_raw)

        return {"hubspot": hubspot_result, "email": email_result}

    # ─────────────────────────────────────────────────────────────────────────
    #  Agent runner
    # ─────────────────────────────────────────────────────────────────────────
    async def _run_agent(self, agent, context: str, session_id: str) -> str:
        log.debug(f"_run_agent() → session_id={session_id!r}  agent={agent!r}")
        runner = Runner(
            agent=agent,
            app_name="sales_copilot",
            session_service=self.session_service,
        )
        response_text = ""

        try:
            async for event in runner.run_async(
                user_id="system",
                session_id=session_id,
                new_message=types.Content(
                    role="user",
                    parts=[types.Part(text=context)],
                ),
            ):
                if event.is_final_response():
                    part = event.content.parts[0]
                    response_text = part.text if hasattr(part, "text") else str(part)
                    log.debug(f"Final response received from session={session_id!r}")
        except Exception:
            log.error(f"_run_agent() runner error for session={session_id!r}:\n" + traceback.format_exc())
            raise

        if not response_text:
            log.warning(f"Agent session={session_id!r} returned empty response text")

        return response_text

    # ─────────────────────────────────────────────────────────────────────────
    #  JSON parser
    # ─────────────────────────────────────────────────────────────────────────
    def _parse_agent_output(self, agent_name: str, output: str) -> Any:
        if not output or not output.strip():
            log.warning(f"[{agent_name}] Empty output — nothing to parse")
            return {"error": "Agent returned empty output"}

        try:
            cleaned = output.strip()

            # Strip markdown code fences if present
            if cleaned.startswith("```"):
                lines   = cleaned.splitlines()
                # Drop first line (```json or ```) and last line (```)
                cleaned = "\n".join(lines[1:-1]).strip()

            parsed = json.loads(cleaned)
            log.info(f"[{agent_name}] JSON parsed OK — type={type(parsed).__name__}")
            return parsed

        except json.JSONDecodeError as exc:
            log.error(
                f"[{agent_name}] JSON decode failed: {exc}\n"
                f"Raw output (first 500 chars): {output[:500]!r}"
            )
            return {"error": "Failed to parse agent JSON output", "raw": output}

    # ─────────────────────────────────────────────────────────────────────────
    #  Context builders
    # ─────────────────────────────────────────────────────────────────────────
    def _build_extraction_context(self, parsed_data: Dict[str, Any]) -> str:
        return f"""
Analyze the following call transcript and extract structured insights:

TRANSCRIPT:
{parsed_data.get('transcript_text', '')}

Return your analysis as JSON.
""".strip()

    def _build_tasks_context(self, parsed_data: Dict[str, Any]) -> str:
        employees = parsed_data.get("internal_employees") or []
        employee_list = ", ".join(employees) if employees else "Unknown"
        return f"""
Analyze the following call transcript and identify action items committed to by internal employees.

INTERNAL EMPLOYEES: {employee_list}

TRANSCRIPT:
{parsed_data.get('transcript_text', '')}

Return the task assignments as JSON.
""".strip()

    def _build_hubspot_context(self, layer1_outputs: Dict[str, Any]) -> str:
        return f"""
Generate CRM field updates based on the following analysis:

EXTRACTION RESULTS:
{json.dumps(layer1_outputs.get('extraction') or {}, indent=2)}

TASK ASSIGNMENTS:
{json.dumps(layer1_outputs.get('tasks') or {}, indent=2)}

Return the CRM update data as JSON.
""".strip()

    def _build_email_context(self, layer1_outputs: Dict[str, Any]) -> str:
        return f"""
Compose a follow-up email based on the following insights:

TOPICS AND PAIN POINTS:
{json.dumps(layer1_outputs.get('extraction') or {}, indent=2)}

ACTION ITEMS ASSIGNED:
{json.dumps(layer1_outputs.get('tasks') or {}, indent=2)}

Return the email as JSON with subject, recipient_email, and email_body fields.
""".strip()

    # ─────────────────────────────────────────────────────────────────────────
    #  Persistence
    # ─────────────────────────────────────────────────────────────────────────
    def _persist_outputs(self, layer2_outputs: Dict[str, Any], meeting_id: Optional[str]) -> None:
        hubspot_data = layer2_outputs.get("hubspot") or {}
        if hubspot_data and not hubspot_data.get("error"):
            try:
                self.storage_service.save_hubspot_payload(hubspot_data, meeting_id)
                log.info(f"HubSpot payload saved — meeting_id={meeting_id!r}")
            except Exception:
                log.error("save_hubspot_payload() failed:\n" + traceback.format_exc())

        email_data = layer2_outputs.get("email") or {}
        if email_data and not email_data.get("error"):
            try:
                self.storage_service.save_email_draft(email_data, meeting_id)
                log.info(f"Email draft saved — meeting_id={meeting_id!r}")
            except Exception:
                log.error("save_email_draft() failed:\n" + traceback.format_exc())

            try:
                self.storage_service.save_mail_payload(email_data, meeting_id)
                log.info(f"Mail payload saved — meeting_id={meeting_id!r}")
            except Exception:
                log.error("save_mail_payload() failed:\n" + traceback.format_exc())

    def save_tasks_to_database(self, tasks_output: Dict[str, Any], meeting_id: Optional[str] = None) -> None:
        tasks = tasks_output.get("tasks") or []
        if not tasks:
            log.warning("save_tasks_to_database() called but no tasks found in output")
            return
        try:
            self.db_service.insert_tasks_batch(tasks, meeting_id)
            log.info(f"Inserted {len(tasks)} task(s) into DB — meeting_id={meeting_id!r}")
        except Exception:
            log.error("insert_tasks_batch() failed:\n" + traceback.format_exc())
            raise