from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, ForeignKey, Enum as SQLEnum, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.enums import ActivityLogEventTypeEnum

class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    event_type: Mapped[ActivityLogEventTypeEnum] = mapped_column(SQLEnum(ActivityLogEventTypeEnum), nullable=False)
    actor_employee_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("employees.id"), nullable=True)
    department_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("departments.id"), nullable=True)
    summary_text: Mapped[str] = mapped_column(String, nullable=False)
    related_entity_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # e.g., "Challenge", "CSRActivity"
    related_entity_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    actor: Mapped[Optional["Employee"]] = relationship("Employee")
    department: Mapped[Optional["Department"]] = relationship("Department")
