from google.adk.agents import LlmAgent
from agents.email_agent.schema import EmailOutput
from agents.email_agent.prompts import SYSTEM_PROMPT
from config import GEMINI_MODEL


def create_email_agent():
    return LlmAgent(
        name = "email_closer_agent",
        model = GEMINI_MODEL,
        description = "Composes professional follow-up emails based on call insights",
        instruction = SYSTEM_PROMPT,
        output_schema = EmailOutput,
        output_key = "agent_4_email"
    )