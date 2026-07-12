from datetime import date
from typing import Optional
from sqlalchemy import String, Integer, ForeignKey, Enum as SQLEnum, Numeric, Date, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.mixins import TimestampMixin
from app.models.enums import CarbonSourceModuleEnum

class CarbonTransaction(Base, TimestampMixin):
    __tablename__ = "carbon_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    department_id: Mapped[int] = mapped_column(Integer, ForeignKey("departments.id"), nullable=False)
    source_module: Mapped[CarbonSourceModuleEnum] = mapped_column(
        SQLEnum(CarbonSourceModuleEnum), nullable=False
    )
    source_reference_id: Mapped[Optional[str]] = mapped_column(String, index=True, nullable=True)
    emission_factor_id: Mapped[int] = mapped_column(Integer, ForeignKey("emission_factors.id"), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(precision=15, scale=4), nullable=False)
    calculated_co2e: Mapped[float] = mapped_column(Numeric(precision=15, scale=4), nullable=False)
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_auto_calculated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by_id: Mapped[int] = mapped_column(Integer, ForeignKey("employees.id"), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    department: Mapped["Department"] = relationship("Department")
    emission_factor: Mapped["EmissionFactor"] = relationship("EmissionFactor")
    created_by: Mapped["Employee"] = relationship("Employee")
