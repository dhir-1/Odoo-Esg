from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing import Optional
from datetime import date, datetime
from app.models.enums import (
    StatusEnum, 
    EmissionActivityTypeEnum, 
    GoalLifecycleStatusEnum, 
    GoalProgressStatusEnum
)

# ==========================================
# EmissionFactor Schemas
# ==========================================

class EmissionFactorCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    activity_type: EmissionActivityTypeEnum
    unit: str = Field(..., min_length=1, max_length=50)
    co2e_per_unit: float = Field(..., ge=0.0)
    category_id: Optional[int] = None
    source_reference: str = Field(..., min_length=1)
    effective_from: date
    effective_to: Optional[date] = None

    @model_validator(mode="after")
    def validate_dates(self) -> "EmissionFactorCreate":
        if self.effective_to and self.effective_to < self.effective_from:
            raise ValueError("effective_to date must be after effective_from date.")
        return self

class EmissionFactorUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=150)
    activity_type: Optional[EmissionActivityTypeEnum] = None
    unit: Optional[str] = Field(default=None, min_length=1, max_length=50)
    co2e_per_unit: Optional[float] = Field(default=None, ge=0.0)
    category_id: Optional[int] = None
    source_reference: Optional[str] = None
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    status: Optional[StatusEnum] = None

    @model_validator(mode="after")
    def validate_dates(self) -> "EmissionFactorUpdate":
        eff_from = self.effective_from
        eff_to = self.effective_to
        if eff_from and eff_to and eff_to < eff_from:
            raise ValueError("effective_to date must be after effective_from date.")
        return self

class EmissionFactorRead(BaseModel):
    id: int
    name: str
    activity_type: EmissionActivityTypeEnum
    unit: str
    co2e_per_unit: float
    category_id: Optional[int]
    source_reference: str
    effective_from: date
    effective_to: Optional[date]
    status: StatusEnum
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# ProductESGProfile Schemas
# ==========================================

class ProductESGProfileCreate(BaseModel):
    product_name: str = Field(..., min_length=1, max_length=150)
    sku: Optional[str] = Field(default=None, max_length=100)
    category: str = Field(..., min_length=1, max_length=100)
    emission_factor_id: Optional[int] = None
    sustainability_score: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    lifecycle_notes: Optional[str] = None

class ProductESGProfileUpdate(BaseModel):
    product_name: Optional[str] = Field(default=None, min_length=1, max_length=150)
    sku: Optional[str] = Field(default=None, max_length=100)
    category: Optional[str] = Field(default=None, min_length=1, max_length=100)
    emission_factor_id: Optional[int] = None
    sustainability_score: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    lifecycle_notes: Optional[str] = None
    status: Optional[StatusEnum] = None

class ProductESGProfileRead(BaseModel):
    id: int
    product_name: str
    sku: Optional[str]
    category: str
    emission_factor_id: Optional[int]
    sustainability_score: Optional[float]
    lifecycle_notes: Optional[str]
    status: StatusEnum
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# EnvironmentalGoal Schemas
# ==========================================

class EnvironmentalGoalCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    department_id: Optional[int] = None
    metric_type: str = Field(..., min_length=1, max_length=100)
    target_value: float = Field(..., ge=0.0)
    current_value: float = Field(default=0.0, ge=0.0)
    unit: str = Field(..., min_length=1, max_length=50)
    start_date: date
    target_date: date

    @model_validator(mode="after")
    def validate_dates(self) -> "EnvironmentalGoalCreate":
        if self.target_date <= self.start_date:
            raise ValueError("target_date must be after start_date.")
        return self

class EnvironmentalGoalUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = None
    department_id: Optional[int] = None
    metric_type: Optional[str] = Field(default=None, min_length=1, max_length=100)
    target_value: Optional[float] = Field(default=None, ge=0.0)
    current_value: Optional[float] = Field(default=None, ge=0.0)
    unit: Optional[str] = Field(default=None, min_length=1, max_length=50)
    start_date: Optional[date] = None
    target_date: Optional[date] = None
    lifecycle_status: Optional[GoalLifecycleStatusEnum] = None

    @model_validator(mode="after")
    def validate_dates(self) -> "EnvironmentalGoalUpdate":
        st = self.start_date
        tgt = self.target_date
        if st and tgt and tgt <= st:
            raise ValueError("target_date must be after start_date.")
        return self

class EnvironmentalGoalRead(BaseModel):
    id: int
    title: str
    description: str
    department_id: Optional[int]
    metric_type: str
    target_value: float
    current_value: float
    unit: str
    start_date: date
    target_date: date
    lifecycle_status: GoalLifecycleStatusEnum
    progress_status: GoalProgressStatusEnum  # Uses the Python property from database model!
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
