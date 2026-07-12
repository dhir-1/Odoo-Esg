from datetime import date
from typing import Optional
from sqlalchemy import String, Integer, ForeignKey, Enum as SQLEnum, Date, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.mixins import TimestampMixin
from app.models.enums import (
    StatusEnum, 
    CSRActivityStatusEnum, 
    ParticipationApprovalStatusEnum, 
    DiversityCategoryEnum, 
    TrainingRecordStatusEnum
)

class CSRActivity(Base, TimestampMixin):
    __tablename__ = "csr_activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey("categories.id"), nullable=False)
    department_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("departments.id"), nullable=True)  # Nullable = Org-wide
    description: Mapped[str] = mapped_column(Text, nullable=False)
    activity_date: Mapped[date] = mapped_column(Date, nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    points_value: Mapped[int] = mapped_column(Integer, nullable=False)
    evidence_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[CSRActivityStatusEnum] = mapped_column(
        SQLEnum(CSRActivityStatusEnum), default=CSRActivityStatusEnum.PLANNED, nullable=False
    )
    created_by_id: Mapped[int] = mapped_column(Integer, ForeignKey("employees.id"), nullable=False)

    # Relationships
    category: Mapped["Category"] = relationship("Category")
    department: Mapped[Optional["Department"]] = relationship("Department")
    created_by: Mapped["Employee"] = relationship("Employee", foreign_keys=[created_by_id])

class EmployeeParticipation(Base, TimestampMixin):
    __tablename__ = "employee_participations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    employee_id: Mapped[int] = mapped_column(Integer, ForeignKey("employees.id"), nullable=False)
    activity_id: Mapped[int] = mapped_column(Integer, ForeignKey("csr_activities.id"), nullable=False)
    proof_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    approval_status: Mapped[ParticipationApprovalStatusEnum] = mapped_column(
        SQLEnum(ParticipationApprovalStatusEnum), default=ParticipationApprovalStatusEnum.PENDING, nullable=False
    )
    points_earned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completion_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    reviewed_by_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("employees.id"), nullable=True)

    # Relationships
    employee: Mapped["Employee"] = relationship("Employee", foreign_keys=[employee_id])
    activity: Mapped["CSRActivity"] = relationship("CSRActivity")
    reviewed_by: Mapped[Optional["Employee"]] = relationship("Employee", foreign_keys=[reviewed_by_id])

class DiversityMetric(Base, TimestampMixin):
    __tablename__ = "diversity_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    department_id: Mapped[int] = mapped_column(Integer, ForeignKey("departments.id"), nullable=False)
    category: Mapped[DiversityCategoryEnum] = mapped_column(SQLEnum(DiversityCategoryEnum), nullable=False)
    label: Mapped[str] = mapped_column(String, nullable=False)  # e.g., "Female", "Male", "Gen Z"
    count: Mapped[int] = mapped_column(Integer, nullable=False)
    period: Mapped[str] = mapped_column(String, nullable=False)  # e.g., "2026-Q3"

    # Relationships
    department: Mapped["Department"] = relationship("Department")

class TrainingRecord(Base, TimestampMixin):
    __tablename__ = "training_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    employee_id: Mapped[int] = mapped_column(Integer, ForeignKey("employees.id"), nullable=False)
    training_name: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    completed_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[TrainingRecordStatusEnum] = mapped_column(
        SQLEnum(TrainingRecordStatusEnum), default=TrainingRecordStatusEnum.ENROLLED, nullable=False
    )
    certificate_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Relationships
    employee: Mapped["Employee"] = relationship("Employee")
