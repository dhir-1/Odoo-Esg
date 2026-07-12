from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, ForeignKey, Enum as SQLEnum, Text, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.enums import NotificationTypeEnum

class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    recipient_id: Mapped[int] = mapped_column(Integer, ForeignKey("employees.id"), nullable=False)
    type: Mapped[NotificationTypeEnum] = mapped_column(SQLEnum(NotificationTypeEnum), nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    related_entity_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # e.g., "ComplianceIssue", "CSRActivity"
    related_entity_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    recipient: Mapped["Employee"] = relationship("Employee")
