from datetime import date
from typing import Optional
from sqlalchemy import String, Integer, Enum as SQLEnum, Date, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.models.mixins import TimestampMixin
from app.models.enums import PolicyStatusEnum, ESGPolicyCategoryEnum

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
