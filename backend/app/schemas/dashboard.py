from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class DashboardSummary(BaseModel):
    environmental_score: float = Field(..., description="Environmental sub-score (0-100)")
    social_score: float = Field(..., description="Social sub-score (0-100)")
    governance_score: float = Field(..., description="Governance sub-score (0-100)")
    overall_esg_score: float = Field(..., description="Overall ESG score (0-100)")

class EmissionsTrendPoint(BaseModel):
    period: str = Field(..., description="Monthly period string in YYYY-MM format")
    co2e: float = Field(..., description="Total CO2e emissions for the period")

class DepartmentRank(BaseModel):
    department_id: int
    department_name: str
    total_score: float
    environmental_score: float
    social_score: float
    governance_score: float

class DashboardActivityLog(BaseModel):
    id: int
    event_type: str
    actor_employee_id: Optional[int] = None
    actor_name: Optional[str] = None
    department_id: Optional[int] = None
    summary_text: str
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True
