from pydantic import BaseModel, Field
from typing import Literal

class HubSpotOutput(BaseModel):
    deal_stage_recommendation: str = Field(description="Next funnel position recommendation")
    perceived_sentiment: str       = Field(description="Assessment of client sentiment")
    competitor_threat_level: Literal["Low", "Medium", "High"] = Field(description="Competitor threat level")
    hubspot_notes_body: str        = Field(description="Consolidated meeting overview paragraph")