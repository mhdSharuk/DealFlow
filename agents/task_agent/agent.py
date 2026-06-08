from google.adk.agents import Agent
from core.config import GEMINI_MODEL
from agents.task_agent.schema import TaskOutput
from agents.task_agent.prompts import SYSTEM_PROMPT

def create_task_agent():
    return Agent(
        name = 'task_agent',
        model = GEMINI_MODEL,
        description = """Maps the call transcript and extracted information to 
                        clear action items for the internal employees
                        to follow up on""",
    instruction = SYSTEM_PROMPT,
    output_schema = TaskOutput,
    output_key = 'agent_2_tasks'
    )