import json
import asyncio
from typing import Dict, Any, Optional

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

class DealFlowOrchestrator:
    def __init__(self):
        self.session_service = InMemorySessionService()
        self.db_service      = DatabaseService()
        self.storage_service = StorageService()

        self.extractor_agent = create_extractor_agent()
        self.taskmage_agent  = create_task_agent()
        self.hubspot_agent   = create_hubspot_agent()
        self.email_agent     = create_email_agent()

    async def process_transcript(self, raw_json: Dict[str, Any]) -> Dict[str, Any]:
        parsed = TranscriptParser.parse_fireflies_json(raw_json)
        meeting_id = parsed["metadata"]["meeting_id"]

        layer1_outputs = await self._execute_layer1_parallel(parsed)

        layer2_outputs = await self._execute_layer2_parallel(layer1_outputs)

        self._persist_outputs(layer2_outputs, meeting_id)

        full_output = {
            "agent_1_extraction": layer1_outputs.get("extraction"),
            "agent_2_tickets": layer1_outputs.get("tasks"),
            "agent_3_hubspot": layer2_outputs.get("hubspot"),
            "agent_4_email": layer2_outputs.get("email"),
            "metadata": parsed["metadata"]
        }

        return full_output

    async def _execute_layer1_parallel(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        extraction_context = self._build_extraction_context(parsed_data)
        tasks_context = self._build_tasks_context(parsed_data)

        extraction_task = self._run_agent(
            self.extractor_agent,
            extraction_context,
            "extraction_session"
        )

        tasks_task = self._run_agent(
            self.taskmage_agent,
            tasks_context,
            "tasks_session"
        )

        results = await asyncio.gather(extraction_task, tasks_task)

        extraction_result = self._parse_agent_output(results[0])
        tasks_result = self._parse_agent_output(results[1])

        return {
            "extraction": extraction_result,
            "tasks": tasks_result
        }

    async def _execute_layer2_parallel(self, layer1_outputs: Dict[str, Any]) -> Dict[str, Any]:
        hubspot_context = self._build_hubspot_context(layer1_outputs)
        email_context = self._build_email_context(layer1_outputs)

        hubspot_task = self._run_agent(
            self.hubspot_agent,
            hubspot_context,
            "hubspot_session"
        )

        email_task = self._run_agent(
            self.email_agent,
            email_context,
            "email_session"
        )

        results = await asyncio.gather(hubspot_task, email_task)

        hubspot_result = self._parse_agent_output(results[0])
        email_result = self._parse_agent_output(results[1])

        return {
            "hubspot": hubspot_result,
            "email": email_result
        }

    async def _run_agent(self, agent, context: str, session_id: str) -> str:
        runner = Runner(agent=agent, app_name="sales_copilot", session_service=self.session_service)
        response_text = ""

        async for event in runner.run_async(
            user_id="system",
            session_id=session_id,
            new_message=types.Content(role="user", parts=[types.Part(text=context)])
        ):
            if event.is_final_response():
                response_text = event.content.parts[0].text if hasattr(event.content.parts[0], "text") else str(event.content.parts[0])

        return response_text

    def _parse_agent_output(self, output: str) -> Any:
        try:
            cleaned = output.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                cleaned = "\n".join(lines[1:-1]) if lines[0].startswith("```") else cleaned
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return {"error": "Failed to parse output", "raw": output}

    def _build_extraction_context(self, parsed_data: Dict[str, Any]) -> str:
        return f"""
            Analyze the following call transcript and extract structured insights:
            TRANSCRIPT:
            {parsed_data['transcript_text']}

            Return your analysis as JSON.
        """

    def _build_tasks_context(self, parsed_data: Dict[str, Any]) -> str:
        employee_list = ", ".join(parsed_data["internal_employees"])
        return f"""
            Analyze the following call transcript and identify action items committed to by internal employees.
            INTERNAL EMPLOYEES: {employee_list}

            TRANSCRIPT:
            {parsed_data['transcript_text']}

            Return the task assignments as JSON.
        """

    def _build_hubspot_context(self, layer1_outputs: Dict[str, Any]) -> str:
        return f"""
            Generate CRM field updates based on the following analysis:

            EXTRACTION RESULTS:
            {json.dumps(layer1_outputs.get('extraction', {}), indent=2)}

            TASK ASSIGNMENTS:
            {json.dumps(layer1_outputs.get('tasks', {}), indent=2)}

            Return the CRM update data as JSON.
        """

    def _build_email_context(self, layer1_outputs: Dict[str, Any]) -> str:
        return f"""
            Compose a follow-up email based on the following insights:

            TOPICS AND PAIN POINTS:
            {json.dumps(layer1_outputs.get('extraction', {}), indent=2)}

            ACTION ITEMS ASSIGNED:
            {json.dumps(layer1_outputs.get('tasks', {}), indent=2)}

            Return the email as JSON with subject, recipient, and body.
        """

    def _persist_outputs(self, layer2_outputs: Dict[str, Any], meeting_id: Optional[str]):
        hubspot_data = layer2_outputs.get("hubspot", {})
        if hubspot_data and not hubspot_data.get("error"):
            self.storage_service.save_hubspot_payload(hubspot_data, meeting_id)

        email_data = layer2_outputs.get("email", {})
        if email_data and not email_data.get("error"):
            self.storage_service.save_email_draft(email_data, meeting_id)
            self.storage_service.save_mail_payload(email_data, meeting_id)

    def save_tasks_to_database(self, tasks_output: Dict[str, Any], meeting_id: Optional[str] = None):
        tasks = tasks_output.get("tasks", [])
        if tasks:
            self.db_service.insert_tasks_batch(tasks, meeting_id)