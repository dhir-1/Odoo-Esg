from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.db.database import get_db
from app.models.gamification import Challenge, ChallengeParticipation
from app.models.category import Category
from app.models.employee import Employee
from app.services.notifications import create_notification
from app.models.enums import (
    RoleEnum,
    ChallengeStatusEnum,
    ParticipationApprovalStatusEnum,
    CategoryTypeEnum,
    NotificationTypeEnum,
    ActivityLogEventTypeEnum
)
from app.core.permissions import get_current_user, require_role
from app.schemas.gamification import (
    ChallengeCreate,
    ChallengeUpdate,
    ChallengeRead,
    ChallengeDetailRead,
    ChallengeParticipationRead,
    ChallengeProgressSubmit
)
from app.services.settings import get_esg_config
from app.services.activity_log import log_activity

router = APIRouter()

@router.post("/challenges/", response_model=ChallengeRead, status_code=status.HTTP_201_CREATED)
async def create_challenge(
    challenge_in: ChallengeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(require_role("Admin", "Manager"))
):
    # Verify category exists and matches type CHALLENGE
    cat_result = await db.execute(select(Category).filter(Category.id == challenge_in.category_id))
    category = cat_result.scalars().first()
    if not category or category.type != CategoryTypeEnum.CHALLENGE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Category ID or category type mismatch."
        )

    new_challenge = Challenge(
        title=challenge_in.title,
        category_id=challenge_in.category_id,
        description=challenge_in.description,
        xp_reward=challenge_in.xp_reward,
        difficulty=challenge_in.difficulty,
        evidence_required=challenge_in.evidence_required,
        deadline=challenge_in.deadline,
        status=ChallengeStatusEnum.DRAFT
    )

    db.add(new_challenge)
    await db.commit()
    await db.refresh(new_challenge)
    return new_challenge

@router.get("/challenges/", response_model=List[ChallengeRead])
async def list_challenges(
    status: Optional[ChallengeStatusEnum] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    query = select(Challenge)

    # Scoping: Employees cannot see Draft challenges
    if current_user.role == RoleEnum.EMPLOYEE:
        query = query.filter(Challenge.status != ChallengeStatusEnum.DRAFT)

    if status:
        # Extra safety for employees trying to explicitly fetch Draft challenges
        if current_user.role == RoleEnum.EMPLOYEE and status == ChallengeStatusEnum.DRAFT:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Employees cannot view draft challenges."
            )
        query = query.filter(Challenge.status == status)

    query = query.offset(offset).limit(limit).order_by(Challenge.id)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/challenges/{id}", response_model=ChallengeDetailRead)
async def get_challenge(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    result = await db.execute(select(Challenge).filter(Challenge.id == id))
    challenge = result.scalars().first()
    if not challenge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Challenge with ID {id} not found."
        )

    # Scope check: Employees cannot see Draft challenges
    if current_user.role == RoleEnum.EMPLOYEE and challenge.status == ChallengeStatusEnum.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Challenge is in Draft state."
        )

    # Compute joined counts and enrollment status
    joined_res = await db.execute(
        select(func.count(ChallengeParticipation.id)).filter(ChallengeParticipation.challenge_id == id)
    )
    joined_count = joined_res.scalar() or 0

    has_joined_res = await db.execute(
        select(ChallengeParticipation).filter(
            ChallengeParticipation.challenge_id == id,
            ChallengeParticipation.employee_id == current_user.id
        )
    )
    has_joined = has_joined_res.scalars().first() is not None

    # Construct validated detail schema
    challenge_dict = {
        col.name: getattr(challenge, col.name) for col in challenge.__table__.columns
    }
    challenge_dict["joined_count"] = joined_count
    challenge_dict["has_joined"] = has_joined

    return ChallengeDetailRead.model_validate(challenge_dict)

@router.patch("/challenges/{id}", response_model=ChallengeRead)
async def update_challenge(
    id: int,
    challenge_in: ChallengeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(require_role("Admin", "Manager"))
):
    result = await db.execute(select(Challenge).filter(Challenge.id == id))
    challenge = result.scalars().first()
    if not challenge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Challenge with ID {id} not found."
        )

    # State Machine checks
    if challenge_in.status is not None:
        current_status = challenge.status
        new_status = challenge_in.status
        if current_status != new_status:
            allowed = False
            if new_status == ChallengeStatusEnum.ARCHIVED:
                allowed = True  # Reachable from any state
            elif current_status == ChallengeStatusEnum.DRAFT and new_status == ChallengeStatusEnum.ACTIVE:
                allowed = True
            elif current_status == ChallengeStatusEnum.ACTIVE and new_status == ChallengeStatusEnum.UNDER_REVIEW:
                allowed = True
            elif current_status == ChallengeStatusEnum.UNDER_REVIEW and new_status == ChallengeStatusEnum.COMPLETED:
                allowed = True

            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid state transition from '{current_status.value}' to '{new_status.value}'."
                )

    update_data = challenge_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(challenge, key, value)

    await db.commit()
    await db.refresh(challenge)
    return challenge

@router.post("/challenges/{id}/join", response_model=ChallengeParticipationRead, status_code=status.HTTP_201_CREATED)
async def join_challenge(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    result = await db.execute(select(Challenge).filter(Challenge.id == id))
    challenge = result.scalars().first()
    if not challenge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Challenge with ID {id} not found."
        )

    # Only ACTIVE challenges can show Join to employees
    if challenge.status != ChallengeStatusEnum.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot join a challenge that is in '{challenge.status.value}' state."
        )

    # Duplicate join check
    dup_res = await db.execute(
        select(ChallengeParticipation).filter(
            ChallengeParticipation.challenge_id == id,
            ChallengeParticipation.employee_id == current_user.id
        )
    )
    if dup_res.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You are already participating in this challenge."
        )

    participation = ChallengeParticipation(
        challenge_id=id,
        employee_id=current_user.id,
        progress=0.0,
        approval_status=ParticipationApprovalStatusEnum.PENDING,
        xp_awarded=0
    )
    db.add(participation)
    await db.commit()
    await db.refresh(participation)
    return participation

@router.patch("/participation/{id}/progress", response_model=ChallengeParticipationRead)
async def submit_challenge_progress(
    id: int,
    progress_in: ChallengeProgressSubmit,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    result = await db.execute(
        select(ChallengeParticipation)
        .options(selectinload(ChallengeParticipation.challenge))
        .filter(ChallengeParticipation.id == id)
    )
    participation = result.scalars().first()
    if not participation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Challenge participation with ID {id} not found."
        )

    if participation.employee_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only submit progress for your own participation."
        )

    participation.progress = progress_in.progress
    if progress_in.proof_url is not None:
        participation.proof_url = progress_in.proof_url
        
    participation.approval_status = ParticipationApprovalStatusEnum.PENDING

    await db.commit()
    await db.refresh(participation)
    return participation

@router.patch("/participation/{id}/approve", response_model=ChallengeParticipationRead)
async def approve_challenge_participation(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(require_role("Admin", "Manager"))
):
    result = await db.execute(
        select(ChallengeParticipation)
        .options(
            selectinload(ChallengeParticipation.employee),
            selectinload(ChallengeParticipation.challenge)
        )
        .filter(ChallengeParticipation.id == id)
    )
    participation = result.scalars().first()
    if not participation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Challenge participation with ID {id} not found."
        )

    if participation.approval_status != ParticipationApprovalStatusEnum.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Participation is already '{participation.approval_status.value}'."
        )

    challenge = participation.challenge
    config = await get_esg_config(db)

    # Evidence required verification
    evidence_required = config.evidence_requirement_enabled or challenge.evidence_required
    if evidence_required and not participation.proof_url:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Approval failed: Evidence proof URL is required but missing."
        )

    # Approve
    participation.approval_status = ParticipationApprovalStatusEnum.APPROVED
    participation.xp_awarded = challenge.xp_reward
    participation.reviewed_by_id = current_user.id

    # Award XP to employee
    employee = participation.employee
    employee.xp_points += challenge.xp_reward

    # Send Notification if enabled
    await create_notification(
        db=db,
        recipient_id=employee.id,
        type=NotificationTypeEnum.APPROVAL_DECISION,
        title="Challenge Completed",
        message=f"Congratulations! Your participation in the challenge '{challenge.title}' was approved! You earned {challenge.xp_reward} XP.",
        related_entity_type="ChallengeParticipation",
        related_entity_id=participation.id
    )

    # Broadcast leaderboard delta to department
    from app.websockets.manager import ws_manager
    await ws_manager.broadcast_to_department(
        department_id=employee.department_id,
        payload={
            "event": "leaderboard_delta",
            "data": {
                "type": "employee",
                "employee_id": employee.id,
                "full_name": employee.full_name,
                "delta": challenge.xp_reward,
                "metric": "xp_points"
            }
        }
    )

    # Log public activity feed
    await log_activity(
        db=db,
        event_type=ActivityLogEventTypeEnum.CHALLENGE_COMPLETED,
        actor_employee_id=employee.id,
        department_id=employee.department_id,
        summary_text=f"{employee.full_name} completed challenge '{challenge.title}'",
        related_entity_type="ChallengeParticipation",
        related_entity_id=participation.id
    )

    await db.commit()
    await db.refresh(participation)

    from app.services.gamification import evaluate_badges_for_employee
    await evaluate_badges_for_employee(db, employee.id)

    return participation

@router.patch("/participation/{id}/reject", response_model=ChallengeParticipationRead)
async def reject_challenge_participation(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(require_role("Admin", "Manager"))
):
    result = await db.execute(
        select(ChallengeParticipation)
        .options(
            selectinload(ChallengeParticipation.employee),
            selectinload(ChallengeParticipation.challenge)
        )
        .filter(ChallengeParticipation.id == id)
    )
    participation = result.scalars().first()
    if not participation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Challenge participation with ID {id} not found."
        )

    if participation.approval_status != ParticipationApprovalStatusEnum.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Participation is already '{participation.approval_status.value}'."
        )

    participation.approval_status = ParticipationApprovalStatusEnum.REJECTED
    participation.xp_awarded = 0
    participation.reviewed_by_id = current_user.id

    # Send Notification if enabled
    await create_notification(
        db=db,
        recipient_id=participation.employee_id,
        type=NotificationTypeEnum.APPROVAL_DECISION,
        title="Challenge Rejected",
        message=f"Your participation in the challenge '{participation.challenge.title}' was rejected.",
        related_entity_type="ChallengeParticipation",
        related_entity_id=participation.id
    )

    await db.commit()
    await db.refresh(participation)
    return participation
