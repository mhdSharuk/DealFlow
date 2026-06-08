from google.adk.agents import LlmAgent
from agents.crm_agent.schema import HubSpotOutput
from agents.crm_agent.prompts import SYSTEM_PROMPT
from core.config import GEMINI_MODEL

def create_hubspot_agent():
    return LlmAgent(
        name          = "hubspot_agent",
        model         = GEMINI_MODEL,
        description   = "Generates CRM field updates and deal positioning recommendations",
        instruction   = SYSTEM_PROMPT,
        output_schema = HubSpotOutput,
        output_key   = "agent_3_hubspot"
    )