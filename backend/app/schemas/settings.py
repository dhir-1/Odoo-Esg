from typing import Optional
from pydantic import BaseModel, Field, model_validator

class ESGConfigurationRead(BaseModel):
    id: int
    environmental_weight: float
    social_weight: float
    governance_weight: float
    auto_emission_calculation_enabled: bool
    evidence_requirement_enabled: bool
    badge_auto_award_enabled: bool
    notify_on_compliance_issue: bool
    notify_on_approval_decision: bool
    notify_on_policy_reminder: bool
    notify_on_badge_unlock: bool

    class Config:
        from_attributes = True

class ESGConfigurationUpdate(BaseModel):
    environmental_weight: Optional[float] = Field(None, ge=0.0, le=1.0)
    social_weight: Optional[float] = Field(None, ge=0.0, le=1.0)
    governance_weight: Optional[float] = Field(None, ge=0.0, le=1.0)
    auto_emission_calculation_enabled: Optional[bool] = None
    evidence_requirement_enabled: Optional[bool] = None
    badge_auto_award_enabled: Optional[bool] = None
    notify_on_compliance_issue: Optional[bool] = None
    notify_on_approval_decision: Optional[bool] = None
    notify_on_policy_reminder: Optional[bool] = None
    notify_on_badge_unlock: Optional[bool] = None

class NotificationPreferencesRead(BaseModel):
    """
    Exposes exactly the four toggles displayed on the settings screen
    in the frontend wireframe.
    """
    auto_emission_calculation_enabled: bool = Field(..., description="Enable auto emission calculation")
    evidence_requirement_enabled: bool = Field(..., description="Require evidence for all CSR activities")
    badge_auto_award_enabled: bool = Field(..., description="Auto-award badges on challenge completion")
    notify_on_compliance_issue: bool = Field(..., description="Email alerts for new compliance issues")

    class Config:
        from_attributes = True

class NotificationPreferencesUpdate(BaseModel):
    auto_emission_calculation_enabled: Optional[bool] = None
    evidence_requirement_enabled: Optional[bool] = None
    badge_auto_award_enabled: Optional[bool] = None
    notify_on_compliance_issue: Optional[bool] = None
