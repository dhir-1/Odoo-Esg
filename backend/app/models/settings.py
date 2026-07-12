from sqlalchemy import Integer, Numeric, Boolean, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.models.mixins import TimestampMixin

class ESGConfiguration(Base, TimestampMixin):
    __tablename__ = "esg_configurations"
    __table_args__ = (
        CheckConstraint("id = 1", name="single_configuration_row"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    environmental_weight: Mapped[float] = mapped_column(Numeric(precision=3, scale=2), default=0.40, nullable=False)
    social_weight: Mapped[float] = mapped_column(Numeric(precision=3, scale=2), default=0.30, nullable=False)
    governance_weight: Mapped[float] = mapped_column(Numeric(precision=3, scale=2), default=0.30, nullable=False)
    auto_emission_calculation_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    evidence_requirement_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    badge_auto_award_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notify_on_compliance_issue: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notify_on_approval_decision: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notify_on_policy_reminder: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notify_on_badge_unlock: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
