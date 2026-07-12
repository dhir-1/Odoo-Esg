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

# ==========================================
# Badge Schemas
# ==========================================
from typing import Dict, Any
from app.models.enums import StatusEnum

class BadgeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1)
    unlock_rule: Dict[str, Any] = Field(..., description="JSON rule specifying unlock conditions")
    icon_url: Optional[str] = Field(default=None, description="Icon asset URL")

class BadgeUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = None
    unlock_rule: Optional[Dict[str, Any]] = None
    icon_url: Optional[str] = None

class BadgeRead(BaseModel):
    id: int
    name: str
    description: str
    unlock_rule: Dict[str, Any]
    icon_url: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# Reward Schemas
# ==========================================

class RewardCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    description: str = Field(..., min_length=1)
    points_required: int = Field(..., ge=0, description="Points required to redeem reward")
    stock: int = Field(..., ge=0, description="Available stock quantity")

class RewardUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=150)
    description: Optional[str] = None
    points_required: Optional[int] = Field(default=None, ge=0)
    stock: Optional[int] = Field(default=None, ge=0)
    status: Optional[StatusEnum] = None

class RewardRead(BaseModel):
    id: int
    name: str
    description: str
    points_required: int
    stock: int
    status: StatusEnum
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EmployeeBadgeRead(BaseModel):
    id: int
    employee_id: int
    badge_id: int
    awarded_at: datetime
    badge: Optional[BadgeRead] = None

    model_config = ConfigDict(from_attributes=True)


class RewardRedemptionRead(BaseModel):
    id: int
    employee_id: int
    reward_id: int
    points_spent: int
    redeemed_at: datetime
    reward: Optional[RewardRead] = None

    model_config = ConfigDict(from_attributes=True)
