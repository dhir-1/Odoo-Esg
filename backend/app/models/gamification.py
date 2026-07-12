from typing import Optional, Dict, Any
from datetime import date, datetime
from sqlalchemy import String, Integer, Enum as SQLEnum, Text, ForeignKey, Date, Numeric, Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.mixins import TimestampMixin
from app.models.enums import StatusEnum, ChallengeDifficultyEnum, ChallengeStatusEnum, ParticipationApprovalStatusEnum

class Badge(Base, TimestampMixin):
    __tablename__ = "badges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    unlock_rule: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    icon_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)

class Reward(Base, TimestampMixin):
    __tablename__ = "rewards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    points_required: Mapped[int] = mapped_column(Integer, nullable=False)
    stock: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[StatusEnum] = mapped_column(
        SQLEnum(StatusEnum), default=StatusEnum.ACTIVE, nullable=False
    )

class Challenge(Base, TimestampMixin):
    __tablename__ = "challenges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey("categories.id"), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    xp_reward: Mapped[int] = mapped_column(Integer, nullable=False)
    difficulty: Mapped[ChallengeDifficultyEnum] = mapped_column(
        SQLEnum(ChallengeDifficultyEnum), default=ChallengeDifficultyEnum.MEDIUM, nullable=False
    )
    evidence_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deadline: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[ChallengeStatusEnum] = mapped_column(
        SQLEnum(ChallengeStatusEnum), default=ChallengeStatusEnum.DRAFT, nullable=False
    )

    # Relationships
    category: Mapped["Category"] = relationship("Category")

class ChallengeParticipation(Base, TimestampMixin):
    __tablename__ = "challenge_participations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    challenge_id: Mapped[int] = mapped_column(Integer, ForeignKey("challenges.id"), nullable=False)
    employee_id: Mapped[int] = mapped_column(Integer, ForeignKey("employees.id"), nullable=False)
    progress: Mapped[float] = mapped_column(Numeric(precision=5, scale=2), default=0.0, nullable=False)  # 0.00 to 100.00
    proof_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    approval_status: Mapped[ParticipationApprovalStatusEnum] = mapped_column(
        SQLEnum(ParticipationApprovalStatusEnum), default=ParticipationApprovalStatusEnum.PENDING, nullable=False
    )
    xp_awarded: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reviewed_by_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("employees.id"), nullable=True)

    # Relationships
    challenge: Mapped["Challenge"] = relationship("Challenge")
    employee: Mapped["Employee"] = relationship("Employee", foreign_keys=[employee_id])
    reviewed_by: Mapped[Optional["Employee"]] = relationship("Employee", foreign_keys=[reviewed_by_id])


class EmployeeBadge(Base):
    __tablename__ = "employee_badges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    employee_id: Mapped[int] = mapped_column(Integer, ForeignKey("employees.id"), nullable=False)
    badge_id: Mapped[int] = mapped_column(Integer, ForeignKey("badges.id"), nullable=False)
    awarded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    employee: Mapped["Employee"] = relationship("Employee", foreign_keys=[employee_id])
    badge: Mapped["Badge"] = relationship("Badge")


class RewardRedemption(Base):
    __tablename__ = "reward_redemptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    employee_id: Mapped[int] = mapped_column(Integer, ForeignKey("employees.id"), nullable=False)
    reward_id: Mapped[int] = mapped_column(Integer, ForeignKey("rewards.id"), nullable=False)
    points_spent: Mapped[int] = mapped_column(Integer, nullable=False)
    redeemed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    employee: Mapped["Employee"] = relationship("Employee", foreign_keys=[employee_id])
    reward: Mapped["Reward"] = relationship("Reward")
