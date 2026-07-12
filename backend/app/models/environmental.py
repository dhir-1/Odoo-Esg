from datetime import date, datetime
from typing import Optional
from sqlalchemy import String, Integer, ForeignKey, Enum as SQLEnum, Numeric, Date, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.mixins import TimestampMixin
from app.models.enums import (
    StatusEnum, 
    EmissionActivityTypeEnum, 
    GoalLifecycleStatusEnum, 
    GoalProgressStatusEnum
)

class EmissionFactor(Base, TimestampMixin):
    __tablename__ = "emission_factors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    activity_type: Mapped[EmissionActivityTypeEnum] = mapped_column(
        SQLEnum(EmissionActivityTypeEnum), nullable=False
    )
    unit: Mapped[str] = mapped_column(String, nullable=False)  # e.g., kg, litre, kWh
    co2e_per_unit: Mapped[float] = mapped_column(Numeric(precision=12, scale=6), nullable=False)
    category_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("categories.id"), nullable=True)
    source_reference: Mapped[str] = mapped_column(Text, nullable=False)  # e.g., "GHG Protocol 2024"
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[StatusEnum] = mapped_column(SQLEnum(StatusEnum), default=StatusEnum.ACTIVE, nullable=False)

    # Relationships
    category: Mapped[Optional["Category"]] = relationship("Category")

class ProductESGProfile(Base, TimestampMixin):
    __tablename__ = "product_esg_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    product_name: Mapped[str] = mapped_column(String, nullable=False)
    sku: Mapped[Optional[str]] = mapped_column(String, unique=True, index=True, nullable=True)
    category: Mapped[str] = mapped_column(String, nullable=False)
    emission_factor_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("emission_factors.id"), nullable=True)
    sustainability_score: Mapped[Optional[float]] = mapped_column(Numeric(precision=5, scale=2), nullable=True)
    lifecycle_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[StatusEnum] = mapped_column(SQLEnum(StatusEnum), default=StatusEnum.ACTIVE, nullable=False)

    # Relationships
    emission_factor: Mapped[Optional[EmissionFactor]] = relationship("EmissionFactor")

class EnvironmentalGoal(Base, TimestampMixin):
    __tablename__ = "environmental_goals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    department_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("departments.id"), nullable=True)  # Nullable = Org-wide
    metric_type: Mapped[str] = mapped_column(String, nullable=False)  # e.g., "Total Emissions"
    target_value: Mapped[float] = mapped_column(Numeric(precision=15, scale=4), nullable=False)
    current_value: Mapped[float] = mapped_column(Numeric(precision=15, scale=4), default=0.0, nullable=False)
    unit: Mapped[str] = mapped_column(String, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    target_date: Mapped[date] = mapped_column(Date, nullable=False)
    lifecycle_status: Mapped[GoalLifecycleStatusEnum] = mapped_column(
        SQLEnum(GoalLifecycleStatusEnum), default=GoalLifecycleStatusEnum.ACTIVE, nullable=False
    )

    # Relationships
    department: Mapped[Optional["Department"]] = relationship("Department")

    @property
    def progress_status(self) -> GoalProgressStatusEnum:
        today = date.today()
        
        # If target has been reached or exceeded
        if float(self.current_value) >= float(self.target_value):
            return GoalProgressStatusEnum.ACHIEVED
            
        if self.lifecycle_status == GoalLifecycleStatusEnum.COMPLETED:
            return GoalProgressStatusEnum.MISSED
            
        if self.lifecycle_status == GoalLifecycleStatusEnum.CANCELLED:
            return GoalProgressStatusEnum.MISSED

        # If date has already expired
        if today >= self.target_date:
            return GoalProgressStatusEnum.MISSED
            
        # Start date safety
        if self.start_date >= self.target_date:
            return GoalProgressStatusEnum.AT_RISK

        # Calculate time ratio and expected progress
        total_days = (self.target_date - self.start_date).days
        elapsed_days = (today - self.start_date).days
        
        if elapsed_days <= 0:
            return GoalProgressStatusEnum.ON_TRACK
            
        time_ratio = min(max(elapsed_days / total_days, 0.0), 1.0)
        expected_progress = float(self.target_value) * time_ratio
        
        if float(self.current_value) >= expected_progress:
            return GoalProgressStatusEnum.ON_TRACK
        else:
            return GoalProgressStatusEnum.AT_RISK
