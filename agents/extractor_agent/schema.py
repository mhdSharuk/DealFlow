from pydantic import BaseModel, Field
from typing import List, Optional

class TopicSummarizer(BaseModel):
    topic_name: str = Field(description="Name of the topic discussed in the transcript")
    summary: str = Field(description="Summary of the discussion related to the topic")

class ExtractionOutputSchema(BaseModel):
    topics: List[TopicSummarizer] = Field(description="List of topics and their summaries extracted from the transcript")
    pain_points: List[str] = Field(description="List of pain points mentioned in the transcript")
    competitors: List[str] = Field( description="List of competitors mentioned in the transcript")