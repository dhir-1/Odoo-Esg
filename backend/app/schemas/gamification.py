from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import ChallengeStatusEnum, ChallengeDifficultyEnum, ParticipationApprovalStatusEnum

class ChallengeCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    category_id: int = Field(..., description="Master category ID")
    description: str = Field(..., min_length=1)
    xp_reward: int = Field(..., ge=0)
    difficulty: ChallengeDifficultyEnum
    evidence_required: bool = Field(default=False)
    deadline: date = Field(..., description="Challenge deadline date")

class ChallengeUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    category_id: Optional[int] = None
    description: Optional[str] = None
    xp_reward: Optional[int] = Field(default=None, ge=0)
    difficulty: Optional[ChallengeDifficultyEnum] = None
    evidence_required: Optional[bool] = None
    deadline: Optional[date] = None
    status: Optional[ChallengeStatusEnum] = None

class ChallengeRead(BaseModel):
    id: int
    title: str
    category_id: int
    description: str
    xp_reward: int
    difficulty: ChallengeDifficultyEnum
    evidence_required: bool
    deadline: date
    status: ChallengeStatusEnum
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ChallengeDetailRead(ChallengeRead):
    joined_count: int = Field(..., description="Number of participants who joined")
    has_joined: bool = Field(..., description="True if the current user is participating")

class ChallengeParticipationRead(BaseModel):
    id: int
    employee_id: int
    challenge_id: int
    progress: float
    proof_url: Optional[str]
    approval_status: ParticipationApprovalStatusEnum
    xp_awarded: int
    reviewed_by_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ChallengeProgressSubmit(BaseModel):
    progress: float = Field(..., ge=0.0, le=100.0, description="Progress value (0.00 to 100.00)")
    proof_url: Optional[str] = Field(default=None, description="URL of the evidence uploaded")
