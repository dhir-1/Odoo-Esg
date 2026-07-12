from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.sql import text
from app.db.database import get_db
from app.models.social import EmployeeParticipation, CSRActivity
from app.models.gamification import ChallengeParticipation, Challenge
from app.models.employee import Employee
from app.models.notification import Notification
from app.models.enums import (
    RoleEnum,
    ParticipationApprovalStatusEnum,
    ActivityLogEventTypeEnum,
    NotificationTypeEnum
)
from app.core.permissions import require_role, has_department_access
from app.schemas.participation import UnifiedParticipationRead
from app.services.activity_log import log_activity
from app.services.settings import get_esg_config

router = APIRouter()

@router.get("/pending", response_model=List[UnifiedParticipationRead])
async def list_pending_participations(
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(require_role("Admin", "Manager"))
):
    # Fetch pending CSR employee participations
    csr_query = (
        select(EmployeeParticipation, Employee, CSRActivity)
        .join(Employee, EmployeeParticipation.employee_id == Employee.id)
        .join(CSRActivity, EmployeeParticipation.activity_id == CSRActivity.id)
        .filter(EmployeeParticipation.approval_status == ParticipationApprovalStatusEnum.PENDING)
    )

    # Fetch pending challenge participations
    challenge_query = (
        select(ChallengeParticipation, Employee, Challenge)
        .join(Employee, ChallengeParticipation.employee_id == Employee.id)
        .join(Challenge, ChallengeParticipation.challenge_id == Challenge.id)
        .filter(ChallengeParticipation.approval_status == ParticipationApprovalStatusEnum.PENDING)
    )

    # Scoping for Managers (only show items where employee is in Manager's department or child departments)
    if current_user.role == RoleEnum.MANAGER:
        subdeps_query = text("""
            WITH RECURSIVE subdeps AS (
                SELECT id FROM departments WHERE id = :manager_dept_id
                UNION ALL
                SELECT d.id FROM departments d JOIN subdeps s ON d.parent_department_id = s.id
            ) SELECT id FROM subdeps;
        """)
        subdeps_res = await db.execute(subdeps_query, {"manager_dept_id": current_user.department_id})
        mgr_dept_ids = [row[0] for row in subdeps_res.fetchall()]

        csr_query = csr_query.filter(Employee.department_id.in_(mgr_dept_ids))
        challenge_query = challenge_query.filter(Employee.department_id.in_(mgr_dept_ids))

    csr_res = await db.execute(csr_query)
    csr_items = csr_res.all()

    challenge_res = await db.execute(challenge_query)
    challenge_items = challenge_res.all()

    unified_list = []

    # Map CSR participations
    for ep, emp, activity in csr_items:
        unified_list.append(UnifiedParticipationRead(
            id=ep.id,
            source_type="csr",
            employee_id=emp.id,
            employee_name=emp.full_name,
            item_title=activity.title,
            proof_url=ep.proof_url,
            points_or_xp=activity.points_value,
            approval_status=ep.approval_status
        ))

    # Map Challenge participations
    for cp, emp, challenge in challenge_items:
        unified_list.append(UnifiedParticipationRead(
            id=cp.id,
            source_type="challenge",
            employee_id=emp.id,
            employee_name=emp.full_name,
            item_title=challenge.title,
            proof_url=cp.proof_url,
            points_or_xp=challenge.xp_reward,
            approval_status=cp.approval_status
        ))

    # Sort unified list by ID to maintain stable ordering
    unified_list.sort(key=lambda x: (x.source_type, x.id))
    return unified_list

@router.patch("/{source_type}/{id}/approve", response_model=UnifiedParticipationRead)
async def approve_unified_participation(
    source_type: str,
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(require_role("Admin", "Manager"))
):
    if source_type not in ("csr", "challenge"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid source type. Must be 'csr' or 'challenge'."
        )

    config = await get_esg_config(db)

    if source_type == "csr":
        part_res = await db.execute(
            select(EmployeeParticipation)
            .filter(EmployeeParticipation.id == id)
        )
        part = part_res.scalars().first()
        if not part:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"CSR participation with ID {id} not found."
            )

        if part.approval_status != ParticipationApprovalStatusEnum.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Participation is already processed."
            )

        activity_res = await db.execute(select(CSRActivity).filter(CSRActivity.id == part.activity_id))
        activity = activity_res.scalars().first()

        emp_res = await db.execute(select(Employee).filter(Employee.id == part.employee_id))
        emp = emp_res.scalars().first()

        # Manager scope checking
        if current_user.role == RoleEnum.MANAGER:
            if not await has_department_access(db, current_user, emp.department_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: Employee is not in your department hierarchy."
                )

        # Evidence required check
        if config.evidence_requirement_enabled and not part.proof_url:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Approval failed: Evidence proof URL is required but missing."
            )

        # Award points & XP
        part.approval_status = ParticipationApprovalStatusEnum.APPROVED
        part.reviewed_by_id = current_user.id
        emp.points_balance += activity.points_value
        emp.xp_points += activity.points_value

        # Notification
        if config.notify_on_approval_decision:
            notif = Notification(
                recipient_id=emp.id,
                type=NotificationTypeEnum.APPROVAL_DECISION,
                title="CSR Activity Approved",
                message=f"Your participation in '{activity.title}' has been approved! You earned {activity.points_value} points.",
                related_entity_type="EmployeeParticipation",
                related_entity_id=part.id
            )
            db.add(notif)

        # Activity log
        await log_activity(
            db=db,
            event_type=ActivityLogEventTypeEnum.CSR_COMPLETED,
            actor_employee_id=emp.id,
            department_id=emp.department_id,
            summary_text=f"{emp.full_name} completed CSR Activity '{activity.title}'",
            related_entity_type="EmployeeParticipation",
            related_entity_id=part.id
        )

        await db.commit()
        await db.refresh(part)

        from app.services.gamification import evaluate_badges_for_employee
        await evaluate_badges_for_employee(db, emp.id)

        return UnifiedParticipationRead(
            id=part.id,
            source_type="csr",
            employee_id=emp.id,
            employee_name=emp.full_name,
            item_title=activity.title,
            proof_url=part.proof_url,
            points_or_xp=activity.points_value,
            approval_status=part.approval_status
        )

    else:  # challenge
        part_res = await db.execute(
            select(ChallengeParticipation)
            .filter(ChallengeParticipation.id == id)
        )
        part = part_res.scalars().first()
        if not part:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Challenge participation with ID {id} not found."
            )

        if part.approval_status != ParticipationApprovalStatusEnum.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Participation is already processed."
            )

        challenge_res = await db.execute(select(Challenge).filter(Challenge.id == part.challenge_id))
        challenge = challenge_res.scalars().first()

        emp_res = await db.execute(select(Employee).filter(Employee.id == part.employee_id))
        emp = emp_res.scalars().first()

        # Manager scope checking
        if current_user.role == RoleEnum.MANAGER:
            if not await has_department_access(db, current_user, emp.department_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: Employee is not in your department hierarchy."
                )

        # Evidence required check
        if config.evidence_requirement_enabled and not part.proof_url:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Approval failed: Evidence proof URL is required but missing."
            )

        # Award XP
        part.approval_status = ParticipationApprovalStatusEnum.APPROVED
        part.reviewed_by_id = current_user.id
        part.xp_awarded = challenge.xp_reward
        emp.xp_points += challenge.xp_reward

        # Notification
        if config.notify_on_approval_decision:
            notif = Notification(
                recipient_id=emp.id,
                type=NotificationTypeEnum.APPROVAL_DECISION,
                title="Challenge Completed",
                message=f"Congratulations! Your participation in the challenge '{challenge.title}' was approved! You earned {challenge.xp_reward} XP.",
                related_entity_type="ChallengeParticipation",
                related_entity_id=part.id
            )
            db.add(notif)

        # Activity log
        await log_activity(
            db=db,
            event_type=ActivityLogEventTypeEnum.CHALLENGE_COMPLETED,
            actor_employee_id=emp.id,
            department_id=emp.department_id,
            summary_text=f"{emp.full_name} completed challenge '{challenge.title}'",
            related_entity_type="ChallengeParticipation",
            related_entity_id=part.id
        )

        await db.commit()
        await db.refresh(part)

        from app.services.gamification import evaluate_badges_for_employee
        await evaluate_badges_for_employee(db, emp.id)

        return UnifiedParticipationRead(
            id=part.id,
            source_type="challenge",
            employee_id=emp.id,
            employee_name=emp.full_name,
            item_title=challenge.title,
            proof_url=part.proof_url,
            points_or_xp=challenge.xp_reward,
            approval_status=part.approval_status
        )

@router.patch("/{source_type}/{id}/reject", response_model=UnifiedParticipationRead)
async def reject_unified_participation(
    source_type: str,
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(require_role("Admin", "Manager"))
):
    if source_type not in ("csr", "challenge"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid source type. Must be 'csr' or 'challenge'."
        )

    config = await get_esg_config(db)

    if source_type == "csr":
        part_res = await db.execute(
            select(EmployeeParticipation)
            .filter(EmployeeParticipation.id == id)
        )
        part = part_res.scalars().first()
        if not part:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"CSR participation with ID {id} not found."
            )

        if part.approval_status != ParticipationApprovalStatusEnum.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Participation is already processed."
            )

        activity_res = await db.execute(select(CSRActivity).filter(CSRActivity.id == part.activity_id))
        activity = activity_res.scalars().first()

        emp_res = await db.execute(select(Employee).filter(Employee.id == part.employee_id))
        emp = emp_res.scalars().first()

        # Manager scope checking
        if current_user.role == RoleEnum.MANAGER:
            if not await has_department_access(db, current_user, emp.department_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: Employee is not in your department hierarchy."
                )

        part.approval_status = ParticipationApprovalStatusEnum.REJECTED
        part.reviewed_by_id = current_user.id

        # Notification
        if config.notify_on_approval_decision:
            notif = Notification(
                recipient_id=emp.id,
                type=NotificationTypeEnum.APPROVAL_DECISION,
                title="CSR Activity Rejected",
                message=f"Your participation in '{activity.title}' has been rejected.",
                related_entity_type="EmployeeParticipation",
                related_entity_id=part.id
            )
            db.add(notif)

        await db.commit()
        await db.refresh(part)

        return UnifiedParticipationRead(
            id=part.id,
            source_type="csr",
            employee_id=emp.id,
            employee_name=emp.full_name,
            item_title=activity.title,
            proof_url=part.proof_url,
            points_or_xp=activity.points_value,
            approval_status=part.approval_status
        )

    else:  # challenge
        part_res = await db.execute(
            select(ChallengeParticipation)
            .filter(ChallengeParticipation.id == id)
        )
        part = part_res.scalars().first()
        if not part:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Challenge participation with ID {id} not found."
            )

        if part.approval_status != ParticipationApprovalStatusEnum.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Participation is already processed."
            )

        challenge_res = await db.execute(select(Challenge).filter(Challenge.id == part.challenge_id))
        challenge = challenge_res.scalars().first()

        emp_res = await db.execute(select(Employee).filter(Employee.id == part.employee_id))
        emp = emp_res.scalars().first()

        # Manager scope checking
        if current_user.role == RoleEnum.MANAGER:
            if not await has_department_access(db, current_user, emp.department_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: Employee is not in your department hierarchy."
                )

        part.approval_status = ParticipationApprovalStatusEnum.REJECTED
        part.reviewed_by_id = current_user.id

        # Notification
        if config.notify_on_approval_decision:
            notif = Notification(
                recipient_id=emp.id,
                type=NotificationTypeEnum.APPROVAL_DECISION,
                title="Challenge Participation Rejected",
                message=f"Your participation in challenge '{challenge.title}' has been rejected.",
                related_entity_type="ChallengeParticipation",
                related_entity_id=part.id
            )
            db.add(notif)

        await db.commit()
        await db.refresh(part)

        return UnifiedParticipationRead(
            id=part.id,
            source_type="challenge",
            employee_id=emp.id,
            employee_name=emp.full_name,
            item_title=challenge.title,
            proof_url=part.proof_url,
            points_or_xp=challenge.xp_reward,
            approval_status=part.approval_status
        )
