from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.employee import Employee
from app.models.gamification import Badge, EmployeeBadge, ChallengeParticipation
from app.models.social import EmployeeParticipation
from app.models.settings import ESGConfiguration
from app.models.notification import Notification
from app.models.enums import ParticipationApprovalStatusEnum, NotificationTypeEnum, ActivityLogEventTypeEnum
from app.services.activity_log import log_activity

async def evaluate_badges_for_employee(db: AsyncSession, employee_id: int):
    # 1. Fetch ESG Configuration
    config_res = await db.execute(select(ESGConfiguration))
    config = config_res.scalars().first()
    if not config or not config.badge_auto_award_enabled:
        return

    # 2. Fetch Employee
    emp_res = await db.execute(select(Employee).filter(Employee.id == employee_id))
    employee = emp_res.scalars().first()
    if not employee:
        return

    # 3. Pull all Badge entries
    badges_res = await db.execute(select(Badge))
    badges = badges_res.scalars().all()

    # 4. Get counts of approved CSR Activity & Challenge participations
    csr_res = await db.execute(
        select(func.count(EmployeeParticipation.id))
        .filter(
            EmployeeParticipation.employee_id == employee_id,
            EmployeeParticipation.approval_status == ParticipationApprovalStatusEnum.APPROVED
        )
    )
    completed_csr_count = csr_res.scalar() or 0

    challenge_res = await db.execute(
        select(func.count(ChallengeParticipation.id))
        .filter(
            ChallengeParticipation.employee_id == employee_id,
            ChallengeParticipation.approval_status == ParticipationApprovalStatusEnum.APPROVED
        )
    )
    completed_challenges_count = challenge_res.scalar() or 0

    # 5. Get already awarded badge IDs
    earned_res = await db.execute(
        select(EmployeeBadge.badge_id).filter(EmployeeBadge.employee_id == employee_id)
    )
    earned_badge_ids = set(earned_res.scalars().all())

    # 6. Evaluate rules
    for badge in badges:
        if badge.id in earned_badge_ids:
            continue

        rule = badge.unlock_rule or {}
        is_unlocked = True

        # Check conditions
        if "xp_threshold" in rule:
            if employee.xp_points < int(rule["xp_threshold"]):
                is_unlocked = False
        if "points_threshold" in rule:
            if employee.points_balance < int(rule["points_threshold"]):
                is_unlocked = False
        if "completed_csr_threshold" in rule:
            if completed_csr_count < int(rule["completed_csr_threshold"]):
                is_unlocked = False
        if "completed_challenges_threshold" in rule:
            if completed_challenges_count < int(rule["completed_challenges_threshold"]):
                is_unlocked = False

        # Award badge
        if is_unlocked:
            # Create link
            new_award = EmployeeBadge(employee_id=employee_id, badge_id=badge.id)
            db.add(new_award)

            # Trigger notification
            new_notification = Notification(
                recipient_id=employee_id,
                type=NotificationTypeEnum.BADGE_UNLOCK,
                title="Badge Unlocked!",
                message=f"Congratulations! You unlocked the badge '{badge.name}': {badge.description}"
            )
            db.add(new_notification)

            # Log activity
            await log_activity(
                db=db,
                event_type=ActivityLogEventTypeEnum.BADGE_AWARDED,
                actor_employee_id=employee_id,
                department_id=employee.department_id,
                summary_text=f"Unlocked badge: {badge.name}"
            )

    await db.commit()
