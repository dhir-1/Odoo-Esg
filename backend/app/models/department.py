from typing import Optional, List
from sqlalchemy import String, Integer, ForeignKey, Enum as SQLEnum
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
