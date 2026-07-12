from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import StatusEnum

class DepartmentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Department name")
    code: str = Field(..., min_length=1, max_length=20, description="Unique department code (e.g. IT, HR)")
    status: StatusEnum = Field(default=StatusEnum.ACTIVE)

class DepartmentCreate(DepartmentBase):
    head_employee_id: Optional[int] = Field(default=None, description="Employee ID of the head of the department")
    parent_department_id: Optional[int] = Field(default=None, description="Parent department ID (for hierarchical mapping)")

class DepartmentUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    code: Optional[str] = Field(default=None, min_length=1, max_length=20)
    status: Optional[StatusEnum] = None
    head_employee_id: Optional[int] = None
    parent_department_id: Optional[int] = None

class DepartmentRead(DepartmentBase):
    id: int
    head_employee_id: Optional[int]
    parent_department_id: Optional[int]
    employee_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
