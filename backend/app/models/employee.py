from datetime import date
from typing import Optional
from sqlalchemy import String, Integer, Date, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.mixins import TimestampMixin
from app.models.enums import StatusEnum, RoleEnum

class Employee(Base, TimestampMixin):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    employee_code: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[RoleEnum] = mapped_column(SQLEnum(RoleEnum), default=RoleEnum.EMPLOYEE, nullable=False)
    department_id: Mapped[int] = mapped_column(Integer, ForeignKey("departments.id"), nullable=False)
    designation: Mapped[str] = mapped_column(String, nullable=False)
    date_joined: Mapped[date] = mapped_column(Date, nullable=False)
    xp_points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    points_balance: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[StatusEnum] = mapped_column(SQLEnum(StatusEnum), default=StatusEnum.ACTIVE, nullable=False)
    avatar_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Relationships
    department: Mapped["Department"] = relationship(
        "Department",
        foreign_keys=[department_id],
        back_populates="employees"
    )
