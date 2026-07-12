from datetime import date, datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class CustomReportFilter(BaseModel):
    department_id: Optional[int] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    module: Optional[str] = Field(None, description="Module type: Environmental, Social, Governance, Gamification")
    employee_id: Optional[int] = None
    challenge_id: Optional[int] = None
    esg_category: Optional[str] = None
    export_format: Optional[str] = Field("json", description="Export format: json, pdf, xlsx, csv")

# Schemas for fixed report outputs

class EnvironmentalReportData(BaseModel):
    total_emissions_co2e: float
    emissions_by_source: Dict[str, float]
    goals: List[Dict[str, Any]]
    product_profiles: List[Dict[str, Any]]

class SocialReportData(BaseModel):
    diversity_breakdown: List[Dict[str, Any]]
    csr_stats: Dict[str, Any]
    training_completion_rate: Dict[str, Any]

class GovernanceReportData(BaseModel):
    policies: List[Dict[str, Any]]
    audits: List[Dict[str, Any]]
    compliance_summary: Dict[str, Any]

class ESGScoreSummary(BaseModel):
    org_total_score: float
    org_environmental_avg: float
    org_social_avg: float
    org_governance_avg: float
    department_comparison: List[Dict[str, Any]]
