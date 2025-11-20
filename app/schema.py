
from pydantic import BaseModel, Field
from typing import List


class TriageRequest(BaseModel):
    description: str = Field(..., min_length=1, max_length=4000)


class RelatedIssue(BaseModel):
    id: str
    title: str
    category: str
    match_score: float


class TriageResponse(BaseModel):
    summary: str
    category: str
    severity: str
    known_issue: bool
    related_issues: List[RelatedIssue]
    next_action: str