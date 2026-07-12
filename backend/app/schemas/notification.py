from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.models.enums import NotificationTypeEnum

class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    recipient_id: int
    type: NotificationTypeEnum
    title: str
    message: str
    is_read: bool
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[int] = None
    created_at: datetime
