from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import text
from app.db.database import get_db
from app.models.social import CSRActivity, EmployeeParticipation
from app.models.category import Category
from app.models.employee import Employee
from app.models.notification import Notification
from app.models.enums import (
    RoleEnum,
    CSRActivityStatusEnum,
    ParticipationApprovalStatusEnum,
    CategoryTypeEnum,
    NotificationTypeEnum,
    ActivityLogEventTypeEnum
)
from app.core.permissions import get_current_user, require_role, has_department_access
from app.schemas.social import (
    CSRActivityCreate,
    CSRActivityUpdate,
    CSRActivityRead,
    CSRActivityDetailRead,
    EmployeeParticipationRead,
    ProofSubmit
)
from app.services.settings import get_esg_config
from app.services.activity_log import log_activity

router = APIRouter()

@router.post("/csr-activities/", response_model=CSRActivityRead, status_code=status.HTTP_201_CREATED)
async def create_csr_activity(
    activity_in: CSRActivityCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(require_role("Admin", "Manager"))
):
    # Scope check for Managers
    if current_user.role == RoleEnum.MANAGER:
        if activity_in.department_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Managers cannot create company-wide activities."
            )
        if not await has_department_access(db, current_user, activity_in.department_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to create activities for this department."
            )

    # Verify category exists and matches type
    cat_result = await db.execute(select(Category).filter(Category.id == activity_in.category_id))
    category = cat_result.scalars().first()
    if not category or category.type != CategoryTypeEnum.CSR_ACTIVITY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Category ID or category type mismatch."
        )

    new_activity = CSRActivity(
        title=activity_in.title,
        category_id=activity_in.category_id,
        department_id=activity_in.department_id,
        description=activity_in.description,
        activity_date=activity_in.activity_date,
        location=activity_in.location,
        points_value=activity_in.points_value,
        evidence_required=activity_in.evidence_required,
        status=CSRActivityStatusEnum.PLANNED,
        created_by_id=current_user.id
    )

    db.add(new_activity)
    await db.commit()
    await db.refresh(new_activity)
    return new_activity

@router.get("/csr-activities/", response_model=List[CSRActivityRead])
async def list_csr_activities(
    status: Optional[CSRActivityStatusEnum] = Query(None),
    department_id: Optional[int] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    query = select(CSRActivity)
    
    # Scoping for Managers
    if current_user.role == RoleEnum.MANAGER:
        # Load manager department hierarchy
        subdeps_query = text("""
            WITH RECURSIVE subdeps AS (
                SELECT id FROM departments WHERE id = :manager_dept_id
                UNION ALL
                SELECT d.id FROM departments d JOIN subdeps s ON d.parent_department_id = s.id
            ) SELECT id FROM subdeps;
        """)
        subdeps_res = await db.execute(subdeps_query, {"manager_dept_id": current_user.department_id})
        mgr_dept_ids = [row[0] for row in subdeps_res.fetchall()]
        
        query = query.filter((CSRActivity.department_id.in_(mgr_dept_ids)) | (CSRActivity.department_id.is_(None)))
    
    # Filter constraints
    if status:
        query = query.filter(CSRActivity.status == status)
    if department_id:
        # If manager requested a department_id, ensure they have access to it
        if current_user.role == RoleEnum.MANAGER:
            if not await has_department_access(db, current_user, department_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to view activities for this department."
                )
        query = query.filter(CSRActivity.department_id == department_id)

    query = query.offset(offset).limit(limit).order_by(CSRActivity.id)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/csr-activities/{id}", response_model=CSRActivityDetailRead)
async def get_csr_activity(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    result = await db.execute(select(CSRActivity).filter(CSRActivity.id == id))
    activity = result.scalars().first()
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"CSR Activity with ID {id} not found."
        )

    # Scope verification for Managers
    if current_user.role == RoleEnum.MANAGER and activity.department_id is not None:
        if not await has_department_access(db, current_user, activity.department_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied for this department's activity."
            )

    # Compute joined counts and participation
    joined_res = await db.execute(
        select(func.count(EmployeeParticipation.id)).filter(EmployeeParticipation.activity_id == id)
    )
    joined_count = joined_res.scalar() or 0

    has_joined_res = await db.execute(
        select(EmployeeParticipation).filter(
            EmployeeParticipation.activity_id == id,
            EmployeeParticipation.employee_id == current_user.id
        )
    )
    has_joined = has_joined_res.scalars().first() is not None

    # Convert activity columns to dict
    activity_dict = {
        col.name: getattr(activity, col.name) for col in activity.__table__.columns
    }
    activity_dict["joined_count"] = joined_count
    activity_dict["has_joined"] = has_joined

    return CSRActivityDetailRead.model_validate(activity_dict)

@router.patch("/csr-activities/{id}", response_model=CSRActivityRead)
async def update_csr_activity(
    id: int,
    activity_in: CSRActivityUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(require_role("Admin", "Manager"))
):
    result = await db.execute(select(CSRActivity).filter(CSRActivity.id == id))
    activity = result.scalars().first()
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"CSR Activity with ID {id} not found."
        )

    # Scope verification for Managers
    if current_user.role == RoleEnum.MANAGER:
        if activity.department_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Managers cannot modify company-wide activities."
            )
        if not await has_department_access(db, current_user, activity.department_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied for this department's activity."
            )

    # Apply changes
    update_data = activity_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(activity, key, value)

    await db.commit()
    await db.refresh(activity)
    return activity

@router.delete("/csr-activities/{id}", response_model=CSRActivityRead)
async def cancel_csr_activity(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(require_role("Admin", "Manager"))
):
    result = await db.execute(select(CSRActivity).filter(CSRActivity.id == id))
    activity = result.scalars().first()
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"CSR Activity with ID {id} not found."
        )

    # Scope verification for Managers
    if current_user.role == RoleEnum.MANAGER:
        if activity.department_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Managers cannot cancel company-wide activities."
            )
        if not await has_department_access(db, current_user, activity.department_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied for this department's activity."
            )

    activity.status = CSRActivityStatusEnum.CANCELLED
    await db.commit()
    await db.refresh(activity)
    return activity

@router.post("/csr-activities/{id}/join", response_model=EmployeeParticipationRead, status_code=status.HTTP_201_CREATED)
async def join_csr_activity(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    result = await db.execute(select(CSRActivity).filter(CSRActivity.id == id))
    activity = result.scalars().first()
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"CSR Activity with ID {id} not found."
        )

    if activity.status == CSRActivityStatusEnum.CANCELLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot join a cancelled activity."
        )

    # Verify duplicate join check
    dup_res = await db.execute(
        select(EmployeeParticipation).filter(
            EmployeeParticipation.activity_id == id,
            EmployeeParticipation.employee_id == current_user.id
        )
    )
    if dup_res.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already joined this activity."
        )

    participation = EmployeeParticipation(
        employee_id=current_user.id,
        activity_id=id,
        approval_status=ParticipationApprovalStatusEnum.PENDING,
        points_earned=0
    )
    db.add(participation)
    await db.commit()
    await db.refresh(participation)
    return participation

@router.patch("/participation/{id}/proof", response_model=EmployeeParticipationRead)
async def submit_participation_proof(
    id: int,
    proof_in: ProofSubmit,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    result = await db.execute(
        select(EmployeeParticipation)
        .options(selectinload(EmployeeParticipation.activity))
        .filter(EmployeeParticipation.id == id)
    )
    participation = result.scalars().first()
    if not participation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Participation record with ID {id} not found."
        )

    if participation.employee_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only submit proof for your own participation."
        )

    participation.proof_url = proof_in.proof_url
    participation.approval_status = ParticipationApprovalStatusEnum.PENDING

    await db.commit()
    await db.refresh(participation)
    return participation

@router.patch("/participation/{id}/approve", response_model=EmployeeParticipationRead)
async def approve_participation(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(require_role("Admin", "Manager"))
):
    result = await db.execute(
        select(EmployeeParticipation)
        .options(
            selectinload(EmployeeParticipation.employee),
            selectinload(EmployeeParticipation.activity)
        )
        .filter(EmployeeParticipation.id == id)
    )
    participation = result.scalars().first()
    if not participation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Participation record with ID {id} not found."
        )

    if participation.approval_status != ParticipationApprovalStatusEnum.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Participation status is already '{participation.approval_status.value}'."
        )

    # Scope check for Managers
    if current_user.role == RoleEnum.MANAGER:
        if not await has_department_access(db, current_user, participation.employee.department_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to approve participations for this employee's department."
            )

    config = await get_esg_config(db)
    activity = participation.activity

    # Evidence required verification
    # Checked if configuration global toggle OR activity specific flag requires evidence
    evidence_required = config.evidence_requirement_enabled or activity.evidence_required
    if evidence_required and not participation.proof_url:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Approval failed: Evidence proof URL is required but missing."
        )

    # Approve
    participation.approval_status = ParticipationApprovalStatusEnum.APPROVED
    participation.points_earned = activity.points_value
    participation.completion_date = date.today()
    participation.reviewed_by_id = current_user.id

    # Award Points and XP to Employee
    employee = participation.employee
    employee.points_balance += activity.points_value
    employee.xp_points += activity.points_value

    # Send Notification if enabled
    if config.notify_on_approval_decision:
        notif = Notification(
            recipient_id=employee.id,
            type=NotificationTypeEnum.APPROVAL_DECISION,
            title="CSR Activity Approved",
            message=f"Your participation in '{activity.title}' has been approved! You earned {activity.points_value} points.",
            is_read=False
        )
        db.add(notif)

    # Log public activity feed
    await log_activity(
        db=db,
        event_type=ActivityLogEventTypeEnum.CSR_COMPLETED,
        actor_employee_id=employee.id,
        department_id=employee.department_id,
        summary_text=f"{employee.full_name} completed '{activity.title}'",
        related_entity_type="EmployeeParticipation",
        related_entity_id=participation.id
    )

    await db.commit()
    await db.refresh(participation)
    return participation

@router.patch("/participation/{id}/reject", response_model=EmployeeParticipationRead)
async def reject_participation(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(require_role("Admin", "Manager"))
):
    result = await db.execute(
        select(EmployeeParticipation)
        .options(
            selectinload(EmployeeParticipation.employee),
            selectinload(EmployeeParticipation.activity)
        )
        .filter(EmployeeParticipation.id == id)
    )
    participation = result.scalars().first()
    if not participation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Participation record with ID {id} not found."
        )

    if participation.approval_status != ParticipationApprovalStatusEnum.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Participation status is already '{participation.approval_status.value}'."
        )

    # Scope check for Managers
    if current_user.role == RoleEnum.MANAGER:
        if not await has_department_access(db, current_user, participation.employee.department_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to reject participations for this employee's department."
            )

    # Reject
    participation.approval_status = ParticipationApprovalStatusEnum.REJECTED
    participation.points_earned = 0
    participation.reviewed_by_id = current_user.id

    # Send Notification if enabled
    config = await get_esg_config(db)
    if config.notify_on_approval_decision:
        notif = Notification(
            recipient_id=participation.employee_id,
            type=NotificationTypeEnum.APPROVAL_DECISION,
            title="CSR Activity Rejected",
            message=f"Your participation in '{participation.activity.title}' has been rejected.",
            is_read=False
        )
        db.add(notif)

    await db.commit()
    await db.refresh(participation)
    return participation
