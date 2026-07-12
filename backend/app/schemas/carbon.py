from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import CarbonSourceModuleEnum

class CarbonTransactionCreate(BaseModel):
    department_id: int = Field(..., description="Target department ID")
    emission_factor_id: int = Field(..., description="Associated emission factor ID")
    quantity: float = Field(..., ge=0.0, description="Quantity of activity unit")
    calculated_co2e: float = Field(..., ge=0.0, description="Pre-calculated CO2e in kg")
    transaction_date: date = Field(..., description="Date of the transaction")
    notes: Optional[str] = Field(default=None)

class CarbonTransactionSimulate(BaseModel):
    department_id: int = Field(..., description="Target department ID")
    emission_factor_id: int = Field(..., description="Associated emission factor ID")
    quantity: float = Field(..., ge=0.0, description="Quantity of activity unit")
    source_module: CarbonSourceModuleEnum = Field(..., description="Originating ERP module")
    source_reference_id: Optional[str] = Field(default=None, description="Originating ERP record unique ID")
    transaction_date: date = Field(..., description="Date of the transaction")
    notes: Optional[str] = Field(default=None)

class CarbonTransactionRead(BaseModel):
    id: int
    department_id: int
    source_module: CarbonSourceModuleEnum
    source_reference_id: Optional[str]
    emission_factor_id: int
    quantity: float
    calculated_co2e: float
    transaction_date: date
    is_auto_calculated: bool
    created_by_id: int
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DepartmentCarbonSummary(BaseModel):
    department_id: int
    department_name: str
    total_co2e: float

    model_config = ConfigDict(from_attributes=True)
