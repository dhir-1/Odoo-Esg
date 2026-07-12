from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import text

from app.db.database import get_db
from app.models.employee import Employee
from app.models.enums import RoleEnum, StatusEnum
from app.core.permissions import require_role
from app.schemas.auth import EmployeeSearchRead

router = APIRouter()

@router.get("/", response_model=List[EmployeeSearchRead])
async def list_employees(
    search: Optional[str] = Query(None, description="Case-insensitive name or email partial match search"),
    department_id: Optional[int] = Query(None, description="Optional department filter"),
    role: Optional[RoleEnum] = Query(None, description="Optional role filter"),
    status: StatusEnum = Query(StatusEnum.ACTIVE, description="Filter status (Active/Inactive)"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(require_role("Admin", "Manager"))
):
    """
    Returns lists of active employees matching query parameters for administrative selection boxes.
    Admin gets visibility org-wide, Managers are constrained to their own sub-department trees.
    Employees do not have access to this endpoint (403 Forbidden).
    """
    query = select(Employee).options(selectinload(Employee.department))

    # RBAC: Manager sees only their department and sub-departments
    if current_user.role == RoleEnum.MANAGER:
        subdeps_query = text("""
            WITH RECURSIVE subdeps AS (
                SELECT id FROM departments WHERE id = :manager_dept_id
                UNION ALL
                SELECT d.id FROM departments d JOIN subdeps s ON d.parent_department_id = s.id
            ) SELECT id FROM subdeps;
        """)
        subdeps_res = await db.execute(subdeps_query, {"manager_dept_id": current_user.department_id})
        allowed_dept_ids = [row[0] for row in subdeps_res.fetchall()]
        
        # Override department_id parameter filter if it's outside manager's sub-tree
        if department_id is not None:
            if department_id not in allowed_dept_ids:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Managers cannot search for employees outside their department hierarchy."
                )
            query = query.filter(Employee.department_id == department_id)
        else:
            query = query.filter(Employee.department_id.in_(allowed_dept_ids))
    else:
        # Admins can query any department
        if department_id is not None:
            query = query.filter(Employee.department_id == department_id)

    # General filters
    query = query.filter(Employee.status == status)
    
    if role:
        query = query.filter(Employee.role == role)
        
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Employee.full_name.ilike(search_term),
                Employee.email.ilike(search_term)
            )
        )

    query = query.offset(offset).limit(limit).order_by(Employee.id)
    res = await db.execute(query)
    employees = res.scalars().all()

    return [
        EmployeeSearchRead(
            id=emp.id,
            full_name=emp.full_name,
            email=emp.email,
            role=emp.role,
            department_id=emp.department_id,
            department_name=emp.department.name if emp.department else None,
            status=emp.status
        ) for emp in employees
    ]
