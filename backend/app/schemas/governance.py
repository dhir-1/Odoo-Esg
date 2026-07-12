from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import PolicyStatusEnum, ESGPolicyCategoryEnum

class ESGPolicyCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    category: ESGPolicyCategoryEnum
    version: str = Field(..., min_length=1, max_length=20)
    document_url: Optional[str] = Field(default=None)
    effective_date: date
    requires_acknowledgement: bool = Field(default=True)

class ESGPolicyUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = None
    category: Optional[ESGPolicyCategoryEnum] = None
    version: Optional[str] = Field(default=None, min_length=1, max_length=20)
    document_url: Optional[str] = None
    effective_date: Optional[date] = None
    requires_acknowledgement: Optional[bool] = None
    status: Optional[PolicyStatusEnum] = None

class ESGPolicyRead(BaseModel):
    id: int
    title: str
    description: str
    category: ESGPolicyCategoryEnum
    version: str
    document_url: Optional[str]
    effective_date: date
    requires_acknowledgement: bool
    status: PolicyStatusEnum
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PolicyAcknowledgementRead(BaseModel):
    id: int
    employee_id: int
    policy_id: int
    acknowledged_at: datetime
    policy_version: str

    model_config = ConfigDict(from_attributes=True)

# Audit Schemas
from app.models.enums import AuditStatusEnum, ComplianceIssueSeverityEnum, ComplianceIssueStatusEnum

class AuditCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    department_id: Optional[int] = Field(default=None, description="Department target constraint (null for company-wide)")
    auditor_id: Optional[int] = Field(default=None, description="Employee ID of the auditor")
    audit_date: date
    scope: str = Field(..., min_length=1)
    findings_summary: Optional[str] = None
    overall_rating: Optional[float] = Field(default=None, ge=0.0, le=100.0)

class AuditUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    department_id: Optional[int] = None
    auditor_id: Optional[int] = None
    audit_date: Optional[date] = None
    scope: Optional[str] = None
    findings_summary: Optional[str] = None
    status: Optional[AuditStatusEnum] = None
    overall_rating: Optional[float] = Field(default=None, ge=0.0, le=100.0)

class AuditRead(BaseModel):
    id: int
    title: str
    department_id: Optional[int] = None
    auditor_id: Optional[int] = None
    audit_date: date
    scope: str
    findings_summary: Optional[str] = None
    status: AuditStatusEnum
    overall_rating: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# ComplianceIssue Schemas
class ComplianceIssueCreate(BaseModel):
    audit_id: Optional[int] = Field(default=None, description="Associated Audit ID")
    description: str = Field(..., min_length=1)
    severity: ComplianceIssueSeverityEnum
    due_date: date = Field(..., description="Action item due date (Required)")
    owner_id: int = Field(..., description="Assigned owner Employee ID (Required)")

class ComplianceIssueUpdate(BaseModel):
    description: Optional[str] = None
    severity: Optional[ComplianceIssueSeverityEnum] = None
    status: Optional[ComplianceIssueStatusEnum] = None
    due_date: Optional[date] = None
    owner_id: Optional[int] = None
    resolution_notes: Optional[str] = None

class ComplianceIssueRead(BaseModel):
    id: int
    audit_id: Optional[int] = None
    description: str
    severity: ComplianceIssueSeverityEnum
    status: ComplianceIssueStatusEnum
    due_date: date
    owner_id: int
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

