from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class DepartmentScoreRead(BaseModel):
    """Serializes a single DepartmentScore row."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    department_id: int
    period_start: date
    period_end: date
    environmental_score: float
    social_score: float
    governance_score: float
    total_score: float
    calculated_at: datetime


class OrgScoreSummary(BaseModel):
    """Aggregated organisation-level ESG score summary."""
    period_start: date
    period_end: date
    total_score: float
    environmental_avg: float
    social_avg: float
    governance_avg: float
    department_count: int
    department_scores: List[DepartmentScoreRead]


class ScoreCalculationResponse(BaseModel):
    """Response wrapper for a POST /scores/calculate trigger."""
    message: str
    score: DepartmentScoreRead
