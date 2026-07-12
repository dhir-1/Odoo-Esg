from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.sql import text
from app.db.database import get_db
from app.models.governance import ESGPolicy, PolicyAcknowledgement
from app.models.employee import Employee
from app.models.enums import (
    RoleEnum,
    PolicyStatusEnum,
    ESGPolicyCategoryEnum,
    StatusEnum,
    ActivityLogEventTypeEnum
)
from app.core.permissions import get_current_user, require_role
from app.schemas.governance import (
    ESGPolicyCreate,
    ESGPolicyUpdate,
    ESGPolicyRead,
    PolicyAcknowledgementRead
)
from app.schemas.auth import EmployeeRead
from app.services.activity_log import log_activity

router = APIRouter()

@router.post("/policies/", response_model=ESGPolicyRead, status_code=status.HTTP_201_CREATED)
async def create_policy(
    policy_in: ESGPolicyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(require_role("Admin"))
):
    new_policy = ESGPolicy(
        title=policy_in.title,
        description=policy_in.description,
        category=policy_in.category,
        version=policy_in.version,
        document_url=policy_in.document_url,
        effective_date=policy_in.effective_date,
        requires_acknowledgement=policy_in.requires_acknowledgement,
        status=PolicyStatusEnum.DRAFT
    )

    db.add(new_policy)
    await db.commit()
    await db.refresh(new_policy)
    return new_policy

@router.get("/policies/", response_model=List[ESGPolicyRead])
async def list_policies(
    status: Optional[PolicyStatusEnum] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    query = select(ESGPolicy)

    # Employees cannot see Draft policies
    if current_user.role == RoleEnum.EMPLOYEE:
        query = query.filter(ESGPolicy.status != PolicyStatusEnum.DRAFT)

    if status:
        if current_user.role == RoleEnum.EMPLOYEE and status == PolicyStatusEnum.DRAFT:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Employees cannot view draft policies."
            )
        query = query.filter(ESGPolicy.status == status)

    query = query.offset(offset).limit(limit).order_by(ESGPolicy.id)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/policies/{id}", response_model=ESGPolicyRead)
async def get_policy(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    result = await db.execute(select(ESGPolicy).filter(ESGPolicy.id == id))
    policy = result.scalars().first()
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy with ID {id} not found."
        )

    # Scope check: Employees cannot see Draft policies
    if current_user.role == RoleEnum.EMPLOYEE and policy.status == PolicyStatusEnum.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Policy is in Draft state."
        )

    return policy

@router.patch("/policies/{id}", response_model=ESGPolicyRead)
async def update_policy(
    id: int,
    policy_in: ESGPolicyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(require_role("Admin"))
):
    result = await db.execute(select(ESGPolicy).filter(ESGPolicy.id == id))
    policy = result.scalars().first()
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy with ID {id} not found."
        )

    update_data = policy_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(policy, key, value)

    await db.commit()
    await db.refresh(policy)
    return policy

@router.post("/policies/{id}/acknowledge", response_model=PolicyAcknowledgementRead, status_code=status.HTTP_201_CREATED)
async def acknowledge_policy(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    # Fetch policy
    result = await db.execute(select(ESGPolicy).filter(ESGPolicy.id == id))
    policy = result.scalars().first()
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy with ID {id} not found."
        )

    # Verify status is Active
    if policy.status != PolicyStatusEnum.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only active policies can be acknowledged."
        )

    # Check duplicate acknowledgement (idempotency checks)
    dup_res = await db.execute(
        select(PolicyAcknowledgement).filter(
            PolicyAcknowledgement.policy_id == id,
            PolicyAcknowledgement.employee_id == current_user.id,
            PolicyAcknowledgement.policy_version == policy.version
        )
    )
    dup = dup_res.scalars().first()
    if dup:
        # Idempotent return of existing acknowledgement
        return dup

    # Create new acknowledgement
    new_ack = PolicyAcknowledgement(
        employee_id=current_user.id,
        policy_id=id,
        policy_version=policy.version
    )
    db.add(new_ack)
    await db.flush()

    # Log public activity
    summary = f"Policy Acknowledged: {policy.title} (v{policy.version})"
    await log_activity(
        db=db,
        event_type=ActivityLogEventTypeEnum.POLICY_ACKNOWLEDGED,
        actor_employee_id=current_user.id,
        department_id=current_user.department_id,
        summary_text=summary,
        related_entity_type="PolicyAcknowledgement",
        related_entity_id=new_ack.id
    )

    await db.commit()
    await db.refresh(new_ack)
    return new_ack

@router.get("/policies/{id}/unacknowledged-employees", response_model=List[EmployeeRead])
async def list_unacknowledged_employees(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(require_role("Admin", "Manager"))
):
    # Fetch policy
    result = await db.execute(select(ESGPolicy).filter(ESGPolicy.id == id))
    policy = result.scalars().first()
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy with ID {id} not found."
        )

    # Subquery checking if employee has acknowledged this specific policy version
    subq = (
        select(1)
        .select_from(PolicyAcknowledgement)
        .filter(
            PolicyAcknowledgement.employee_id == Employee.id,
            PolicyAcknowledgement.policy_id == id,
            PolicyAcknowledgement.policy_version == policy.version
        )
    ).exists()

    query = select(Employee).filter(Employee.status == StatusEnum.ACTIVE, ~subq)

    # Scoping for Managers (Manager department and child sub-departments)
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
        
        query = query.filter(Employee.department_id.in_(mgr_dept_ids))

    result = await db.execute(query)
    return result.scalars().all()
