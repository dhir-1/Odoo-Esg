from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.sql import text
from app.db.database import get_db
from app.models.governance import ESGPolicy, PolicyAcknowledgement, Audit, ComplianceIssue
from app.models.employee import Employee
from app.services.notifications import create_notification
from app.models.enums import (
    RoleEnum,
    PolicyStatusEnum,
    ESGPolicyCategoryEnum,
    StatusEnum,
    ActivityLogEventTypeEnum,
    AuditStatusEnum,
    ComplianceIssueSeverityEnum,
    ComplianceIssueStatusEnum,
    NotificationTypeEnum
)
from app.core.permissions import get_current_user, require_role, has_department_access
from app.schemas.governance import (
    ESGPolicyCreate,
    ESGPolicyUpdate,
    ESGPolicyRead,
    PolicyAcknowledgementRead,
    AuditCreate,
    AuditUpdate,
    AuditRead,
    ComplianceIssueCreate,
    ComplianceIssueUpdate,
    ComplianceIssueRead
)
from app.schemas.auth import EmployeeRead
from app.services.activity_log import log_activity
from app.services.settings import get_esg_config

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


# ==========================================
# Audit CRUD Endpoints
# ==========================================

@router.post("/audits/", response_model=AuditRead, status_code=status.HTTP_201_CREATED)
async def create_audit(
    audit_in: AuditCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(require_role("Admin", "Manager"))
):
    # Manager scope checking
    if current_user.role == RoleEnum.MANAGER:
        if audit_in.department_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Managers cannot create company-wide audits."
            )
        if not await has_department_access(db, current_user, audit_in.department_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to create audits for this department."
            )

    # Verify auditor exists if provided
    if audit_in.auditor_id is not None:
        auditor_res = await db.execute(select(Employee).filter(Employee.id == audit_in.auditor_id))
        if not auditor_res.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Auditor employee with ID {audit_in.auditor_id} not found."
            )

    new_audit = Audit(
        title=audit_in.title,
        department_id=audit_in.department_id,
        auditor_id=audit_in.auditor_id,
        audit_date=audit_in.audit_date,
        scope=audit_in.scope,
        findings_summary=audit_in.findings_summary,
        overall_rating=audit_in.overall_rating,
        status=AuditStatusEnum.SCHEDULED
    )

    db.add(new_audit)
    await db.commit()
    await db.refresh(new_audit)
    return new_audit

@router.get("/audits/", response_model=List[AuditRead])
async def list_audits(
    status: Optional[AuditStatusEnum] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    query = select(Audit)

    # Managers see their own department audits (and sub-departments) and company-wide
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
        query = query.filter((Audit.department_id.in_(mgr_dept_ids)) | (Audit.department_id.is_(None)))

    if status:
        query = query.filter(Audit.status == status)

    query = query.offset(offset).limit(limit).order_by(Audit.id)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/audits/{id}", response_model=AuditRead)
async def get_audit(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    result = await db.execute(select(Audit).filter(Audit.id == id))
    audit = result.scalars().first()
    if not audit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit with ID {id} not found."
        )

    # Manager scope checking
    if current_user.role == RoleEnum.MANAGER and audit.department_id is not None:
        if not await has_department_access(db, current_user, audit.department_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this audit."
            )

    return audit

@router.patch("/audits/{id}", response_model=AuditRead)
async def update_audit(
    id: int,
    audit_in: AuditUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(require_role("Admin", "Manager"))
):
    result = await db.execute(select(Audit).filter(Audit.id == id))
    audit = result.scalars().first()
    if not audit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit with ID {id} not found."
        )

    # Manager scope checking
    if current_user.role == RoleEnum.MANAGER:
        if audit.department_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Managers cannot modify company-wide audits."
            )
        if not await has_department_access(db, current_user, audit.department_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this audit."
            )

    update_data = audit_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(audit, key, value)

    await db.commit()
    await db.refresh(audit)
    return audit


# ==========================================
# ComplianceIssue CRUD Endpoints
# ==========================================

@router.post("/compliance-issues/", response_model=ComplianceIssueRead, status_code=status.HTTP_201_CREATED)
async def create_compliance_issue(
    issue_in: ComplianceIssueCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(require_role("Admin", "Manager"))
):
    # Verify owner employee exists
    owner_res = await db.execute(select(Employee).filter(Employee.id == issue_in.owner_id))
    owner = owner_res.scalars().first()
    if not owner:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Owner employee with ID {issue_in.owner_id} not found."
        )

    # Verify audit exists if audit_id is provided
    if issue_in.audit_id is not None:
        audit_res = await db.execute(select(Audit).filter(Audit.id == issue_in.audit_id))
        audit = audit_res.scalars().first()
        if not audit:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Audit with ID {issue_in.audit_id} not found."
            )
        # If manager, verify they have access to the audit department
        if current_user.role == RoleEnum.MANAGER and audit.department_id is not None:
            if not await has_department_access(db, current_user, audit.department_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot create compliance issue for an audit outside your department."
                )

    # If manager, verify they have access to the owner's department
    if current_user.role == RoleEnum.MANAGER:
        if not await has_department_access(db, current_user, owner.department_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot assign compliance issues to employees outside your department hierarchy."
            )

    new_issue = ComplianceIssue(
        audit_id=issue_in.audit_id,
        description=issue_in.description,
        severity=issue_in.severity,
        status=ComplianceIssueStatusEnum.OPEN,
        due_date=issue_in.due_date,
        owner_id=issue_in.owner_id
    )

    db.add(new_issue)
    await db.flush()

    # Trigger Notification to owner if enabled
    await create_notification(
        db=db,
        recipient_id=issue_in.owner_id,
        type=NotificationTypeEnum.COMPLIANCE_ISSUE,
        title="Compliance Issue Assigned",
        message=f"You have been assigned a new compliance issue: '{issue_in.description}' (Due: {issue_in.due_date}).",
        related_entity_type="ComplianceIssue",
        related_entity_id=new_issue.id
    )

    # Log public activity
    await log_activity(
        db=db,
        event_type=ActivityLogEventTypeEnum.COMPLIANCE_ISSUE_RAISED,
        actor_employee_id=current_user.id,
        department_id=owner.department_id,
        summary_text=f"Compliance Issue raised for {owner.full_name}: '{issue_in.description}'",
        related_entity_type="ComplianceIssue",
        related_entity_id=new_issue.id
    )

    await db.commit()
    await db.refresh(new_issue)
    return new_issue

@router.get("/compliance-issues/overdue", response_model=List[ComplianceIssueRead])
async def list_overdue_compliance_issues(
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    query = select(ComplianceIssue).filter(
        ComplianceIssue.due_date < date.today(),
        ComplianceIssue.status == ComplianceIssueStatusEnum.OPEN
    )

    # Scoping for Managers
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

        # Filter by owner department or audit department in hierarchy
        query = query.join(Employee, ComplianceIssue.owner_id == Employee.id).outerjoin(Audit, ComplianceIssue.audit_id == Audit.id)
        query = query.filter(
            (Employee.department_id.in_(mgr_dept_ids)) |
            (Audit.department_id.in_(mgr_dept_ids))
        )

    result = await db.execute(query)
    return result.scalars().all()

@router.get("/compliance-issues/", response_model=List[ComplianceIssueRead])
async def list_compliance_issues(
    status: Optional[ComplianceIssueStatusEnum] = Query(None),
    severity: Optional[ComplianceIssueSeverityEnum] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    query = select(ComplianceIssue)

    # Scoping for Managers
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

        query = query.join(Employee, ComplianceIssue.owner_id == Employee.id).outerjoin(Audit, ComplianceIssue.audit_id == Audit.id)
        query = query.filter(
            (Employee.department_id.in_(mgr_dept_ids)) |
            (Audit.department_id.in_(mgr_dept_ids))
        )

    if status:
        query = query.filter(ComplianceIssue.status == status)
    if severity:
        query = query.filter(ComplianceIssue.severity == severity)

    query = query.offset(offset).limit(limit).order_by(ComplianceIssue.id)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/compliance-issues/{id}", response_model=ComplianceIssueRead)
async def get_compliance_issue(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    result = await db.execute(
        select(ComplianceIssue)
        .options(selectinload(ComplianceIssue.owner), selectinload(ComplianceIssue.audit))
        .filter(ComplianceIssue.id == id)
    )
    issue = result.scalars().first()
    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Compliance Issue with ID {id} not found."
        )

    # Scoping for Managers
    if current_user.role == RoleEnum.MANAGER:
        # Check access recursively
        has_access = False
        if issue.owner_id and await has_department_access(db, current_user, issue.owner.department_id):
            has_access = True
        elif issue.audit_id and issue.audit.department_id and await has_department_access(db, current_user, issue.audit.department_id):
            has_access = True
            
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this compliance issue."
            )

    return issue

@router.patch("/compliance-issues/{id}", response_model=ComplianceIssueRead)
async def update_compliance_issue(
    id: int,
    issue_in: ComplianceIssueUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(require_role("Admin", "Manager"))
):
    result = await db.execute(
        select(ComplianceIssue)
        .options(selectinload(ComplianceIssue.owner), selectinload(ComplianceIssue.audit))
        .filter(ComplianceIssue.id == id)
    )
    issue = result.scalars().first()
    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Compliance Issue with ID {id} not found."
        )

    # Scoping for Managers
    if current_user.role == RoleEnum.MANAGER:
        has_access = False
        if issue.owner_id and await has_department_access(db, current_user, issue.owner.department_id):
            has_access = True
        elif issue.audit_id and issue.audit.department_id and await has_department_access(db, current_user, issue.audit.department_id):
            has_access = True
            
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this compliance issue."
            )

    # Apply updates
    update_data = issue_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(issue, key, value)

    # If status changes to RESOLVED or CLOSED, set resolved_at
    if issue_in.status in {ComplianceIssueStatusEnum.RESOLVED, ComplianceIssueStatusEnum.CLOSED}:
        issue.resolved_at = datetime.utcnow()

    await db.commit()
    await db.refresh(issue)
    return issue
