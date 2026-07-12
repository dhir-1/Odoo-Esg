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
