from google.adk.agents import LlmAgent
from config import GEMINI_MODEL
from agents.extractor_agent.prompts import EXTRACTOR_AGENT_PROMPT
from agents.extractor_agent.schema import ExtractionOutputSchema

def create_extractor_agent():
    return LlmAgent(
        name = 'extractor_agent',
        model = GEMINI_MODEL,
        description = """Extracts topics and its summaries along with 
                        pain points and competitiors mentioned from
                        the call transcripts""",
        instructions = EXTRACTOR_AGENT_PROMPT,
        output_schema = ExtractionOutputSchema,
        output_key = 'extraction_result'
    )