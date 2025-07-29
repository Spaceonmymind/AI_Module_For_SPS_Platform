from pydantic import BaseModel
from typing import Dict, Union


class AIBlock(BaseModel):
    verdict: str
    sources: Dict[str, Union[str, dict]]


class FinalOutput(BaseModel):
    structure_validation: dict
    ai_detection: AIBlock
    freshness_check: dict
    similar_ideas: dict
    quality_evaluation: dict
