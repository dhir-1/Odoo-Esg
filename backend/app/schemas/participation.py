from pydantic import BaseModel, ConfigDict
from typing import Optional
from app.models.enums import ParticipationApprovalStatusEnum

class UnifiedParticipationRead(BaseModel):
    id: int
    source_type: str  # "csr" or "challenge"
    employee_id: int
    employee_name: str
    item_title: str
    proof_url: Optional[str] = None
    points_or_xp: int
    approval_status: ParticipationApprovalStatusEnum

    model_config = ConfigDict(from_attributes=True)
