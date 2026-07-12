from typing import Optional, List
from datetime import date, datetime
from sqlalchemy import String, Integer, ForeignKey, Enum as SQLEnum, Date, DateTime, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.mixins import TimestampMixin
from app.models.enums import StatusEnum

class Department(Base, TimestampMixin):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    code: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    head_employee_id: Mapped[Optional[int]] = mapped_column(
        Integer, 
        ForeignKey("employees.id", use_alter=True, name="fk_department_head"), 
        nullable=True
    )
    parent_department_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("departments.id"), nullable=True
    )
    employee_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[StatusEnum] = mapped_column(
        SQLEnum(StatusEnum), default=StatusEnum.ACTIVE, nullable=False
    )

    # Relationships
    head_employee: Mapped[Optional["Employee"]] = relationship(
        "Employee",
        foreign_keys=[head_employee_id],
        post_update=True
    )
    parent_department: Mapped[Optional["Department"]] = relationship(
        "Department",
        remote_side=[id],
        back_populates="sub_departments"
    )
    sub_departments: Mapped[List["Department"]] = relationship(
        "Department",
        back_populates="parent_department"
    )
    employees: Mapped[List["Employee"]] = relationship(
        "Employee",
        foreign_keys="[Employee.department_id]",
        back_populates="department"
    )

    @property
    def head_employee_name(self) -> Optional[str]:
        return self.head_employee.full_name if self.head_employee else None

    @property
    def parent_department_name(self) -> Optional[str]:
        return self.parent_department.name if self.parent_department else None


class DepartmentScore(Base):
    __tablename__ = "department_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    department_id: Mapped[int] = mapped_column(Integer, ForeignKey("departments.id"), nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    environmental_score: Mapped[float] = mapped_column(Numeric(precision=5, scale=2), nullable=False)
    social_score: Mapped[float] = mapped_column(Numeric(precision=5, scale=2), nullable=False)
    governance_score: Mapped[float] = mapped_column(Numeric(precision=5, scale=2), nullable=False)
    total_score: Mapped[float] = mapped_column(Numeric(precision=5, scale=2), nullable=False)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Relationships
    department: Mapped["Department"] = relationship("Department")
