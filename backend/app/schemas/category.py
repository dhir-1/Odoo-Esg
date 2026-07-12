from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime
from app.models.enums import StatusEnum, CategoryTypeEnum

class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    type: CategoryTypeEnum

class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    type: Optional[CategoryTypeEnum] = None
    status: Optional[StatusEnum] = None

class CategoryRead(BaseModel):
    id: int
    name: str
    type: CategoryTypeEnum
    status: StatusEnum
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
