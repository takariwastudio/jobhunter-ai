import uuid
from typing import List, Optional
from pydantic import BaseModel


class JobInput(BaseModel):
    external_id: str
    title: str
    company: str
    description: str


class MatchScore(BaseModel):
    external_id: str
    score: int
    reasoning: str
    matching_skills: List[str]
    missing_skills: List[str]
    recommendation: str  # strong_match | good_match | partial_match | weak_match


class MatchRequest(BaseModel):
    cv_id: uuid.UUID
    jobs: List[JobInput]


class MatchResponse(BaseModel):
    results: List[MatchScore]
    profile_name: Optional[str] = None
