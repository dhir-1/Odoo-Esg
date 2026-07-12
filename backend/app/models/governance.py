from datetime import date, datetime
from typing import Optional
from sqlalchemy import String, Integer, Enum as SQLEnum, Date, Text, Boolean, DateTime, ForeignKey, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.mixins import TimestampMixin
from app.models.enums import (
    PolicyStatusEnum, 
    ESGPolicyCategoryEnum, 
    AuditStatusEnum, 
    ComplianceIssueSeverityEnum, 
    ComplianceIssueStatusEnum
)

class ESGPolicy(Base, TimestampMixin):
    __tablename__ = "esg_policies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[ESGPolicyCategoryEnum] = mapped_column(
        SQLEnum(ESGPolicyCategoryEnum), nullable=False
    )
    version: Mapped[str] = mapped_column(String, nullable=False)
    document_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)
    requires_acknowledgement: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status: Mapped[PolicyStatusEnum] = mapped_column(
        SQLEnum(PolicyStatusEnum), default=PolicyStatusEnum.DRAFT, nullable=False
    )

class PolicyAcknowledgement(Base):
    __tablename__ = "policy_acknowledgements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    employee_id: Mapped[int] = mapped_column(Integer, ForeignKey("employees.id"), nullable=False)
    policy_id: Mapped[int] = mapped_column(Integer, ForeignKey("esg_policies.id"), nullable=False)
    acknowledged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    policy_version: Mapped[str] = mapped_column(String, nullable=False)

    # Relationships
    employee: Mapped["Employee"] = relationship("Employee")
    policy: Mapped["ESGPolicy"] = relationship("ESGPolicy")

class Audit(Base, TimestampMixin):
    __tablename__ = "audits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    department_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("departments.id"), nullable=True)  # Nullable = Org-wide
    auditor_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("employees.id"), nullable=True)
    audit_date: Mapped[date] = mapped_column(Date, nullable=False)
    scope: Mapped[str] = mapped_column(Text, nullable=False)
    findings_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[AuditStatusEnum] = mapped_column(
        SQLEnum(AuditStatusEnum), default=AuditStatusEnum.SCHEDULED, nullable=False
    )
    overall_rating: Mapped[Optional[float]] = mapped_column(Numeric(precision=4, scale=2), nullable=True)

    # Relationships
    department: Mapped[Optional["Department"]] = relationship("Department")
    auditor: Mapped[Optional["Employee"]] = relationship("Employee")

class ComplianceIssue(Base, TimestampMixin):
    __tablename__ = "compliance_issues"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    audit_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("audits.id"), nullable=True)
    severity: Mapped[ComplianceIssueSeverityEnum] = mapped_column(
        SQLEnum(ComplianceIssueSeverityEnum), nullable=False
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    owner_id: Mapped[int] = mapped_column(Integer, ForeignKey("employees.id"), nullable=False)  # Enforce at DB level
    due_date: Mapped[date] = mapped_column(Date, nullable=False)  # Enforce at DB level
    status: Mapped[ComplianceIssueStatusEnum] = mapped_column(
        SQLEnum(ComplianceIssueStatusEnum), default=ComplianceIssueStatusEnum.OPEN, nullable=False
    )

    # Relationships
    audit: Mapped[Optional["Audit"]] = relationship("Audit")
    owner: Mapped["Employee"] = relationship("Employee")
