from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import CSRActivityStatusEnum, ParticipationApprovalStatusEnum

class CSRActivityCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    category_id: int = Field(..., description="Master category ID")
    department_id: Optional[int] = Field(default=None, description="Department target constraint (null for company-wide)")
    description: str = Field(..., min_length=1)
    activity_date: date = Field(..., description="Activity date")
    location: Optional[str] = Field(default=None)
    points_value: int = Field(..., ge=0, description="Points awarded on completion")
    evidence_required: bool = Field(default=False, description="Whether proof is required to approve participation")

class CSRActivityUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    category_id: Optional[int] = None
    department_id: Optional[int] = None
    description: Optional[str] = None
    activity_date: Optional[date] = None
    location: Optional[str] = None
    points_value: Optional[int] = Field(default=None, ge=0)
    evidence_required: Optional[bool] = None
    status: Optional[CSRActivityStatusEnum] = None

class CSRActivityRead(BaseModel):
    id: int
    title: str
    category_id: int
    department_id: Optional[int]
    description: str
    activity_date: date
    location: Optional[str]
    points_value: int
    evidence_required: bool
    status: CSRActivityStatusEnum
    created_by_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class CSRActivityDetailRead(CSRActivityRead):
    joined_count: int = Field(..., description="Number of participants who joined")
    has_joined: bool = Field(..., description="True if the current user is participating")

class EmployeeParticipationRead(BaseModel):
    id: int
    employee_id: int
    activity_id: int
    proof_url: Optional[str]
    approval_status: ParticipationApprovalStatusEnum
    points_earned: int
    completion_date: Optional[date]
    reviewed_by_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ProofSubmit(BaseModel):
    proof_url: str = Field(..., min_length=1, description="URL of the evidence uploaded")

