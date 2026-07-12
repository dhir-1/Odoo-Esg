from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.database import get_db
from app.models.department import Department
from app.models.employee import Employee
from app.models.enums import StatusEnum
from app.core.permissions import get_current_user, require_role
from app.schemas.department import DepartmentCreate, DepartmentUpdate, DepartmentRead

router = APIRouter()

async def is_ancestor(db: AsyncSession, department_id: int, potential_ancestor_id: int) -> bool:
    """
    Checks if potential_ancestor_id is a parent (or ancestor) of department_id.
    Prevents circular hierarchy loops.
    """
    curr_id = department_id
    visited = set()
    while curr_id is not None:
        if curr_id == potential_ancestor_id:
            return True
        if curr_id in visited:
            break  # Prevent infinite loop if a cycle already exists somehow
        visited.add(curr_id)
        
        result = await db.execute(select(Department.parent_department_id).filter(Department.id == curr_id))
        curr_id = result.scalar()
    return False

@router.post("/", response_model=DepartmentRead, status_code=status.HTTP_201_CREATED)
async def create_department(
    dept_in: DepartmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(require_role("Admin"))
):
    # Check duplicate code
    dup_result = await db.execute(select(Department).filter(Department.code == dept_in.code))
    dup = dup_result.scalars().first()
    if dup:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Department with code '{dept_in.code}' already exists."
        )

    # Check parent department exists
    if dept_in.parent_department_id is not None:
        parent_result = await db.execute(select(Department).filter(Department.id == dept_in.parent_department_id))
        parent = parent_result.scalars().first()
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Parent department with ID {dept_in.parent_department_id} does not exist."
            )

    # Check head employee exists
    if dept_in.head_employee_id is not None:
        head_result = await db.execute(select(Employee).filter(Employee.id == dept_in.head_employee_id))
        head = head_result.scalars().first()
        if not head:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Head employee with ID {dept_in.head_employee_id} does not exist."
            )

    new_dept = Department(
        name=dept_in.name,
        code=dept_in.code,
        status=dept_in.status,
        parent_department_id=dept_in.parent_department_id,
        head_employee_id=dept_in.head_employee_id,
        employee_count=0
    )
    db.add(new_dept)
    await db.commit()
    res = await db.execute(
        select(Department)
        .options(selectinload(Department.head_employee), selectinload(Department.parent_department))
        .filter(Department.id == new_dept.id)
    )
    return res.scalars().first()

@router.get("/public", summary="Public department list for signup dropdowns")
async def list_departments_public(
    db: AsyncSession = Depends(get_db),
):
    """
    Returns a lightweight list of active departments (id, name, code)
    without requiring authentication. Used by the signup form dropdown.
    """
    query = (
        select(Department.id, Department.name, Department.code)
        .filter(Department.status == StatusEnum.ACTIVE)
        .order_by(Department.name)
    )
    result = await db.execute(query)
    rows = result.all()
    return [{"id": r.id, "name": r.name, "code": r.code, "status": "Active"} for r in rows]


@router.get("/", response_model=List[DepartmentRead])
async def list_departments(
    status: Optional[StatusEnum] = Query(None, description="Filter by active/inactive status"),
    limit: int = Query(10, ge=1, le=100, description="Page limit size"),
    offset: int = Query(0, ge=0, description="Offset count"),
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    query = select(Department).options(
        selectinload(Department.head_employee),
        selectinload(Department.parent_department)
    )
    if status is not None:
        query = query.filter(Department.status == status)
    
    query = query.offset(offset).limit(limit).order_by(Department.id)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{id}", response_model=DepartmentRead)
async def get_department(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    result = await db.execute(
        select(Department)
        .options(selectinload(Department.head_employee), selectinload(Department.parent_department))
        .filter(Department.id == id)
    )
    dept = result.scalars().first()
    if not dept:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Department with ID {id} not found."
        )
    return dept

@router.patch("/{id}", response_model=DepartmentRead)
async def update_department(
    id: int,
    dept_in: DepartmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(require_role("Admin"))
):
    # Fetch department
    result = await db.execute(select(Department).filter(Department.id == id))
    dept = result.scalars().first()
    if not dept:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Department with ID {id} not found."
        )

    # Check duplicate code if code is changing
    if dept_in.code is not None and dept_in.code != dept.code:
        dup_result = await db.execute(select(Department).filter(Department.code == dept_in.code))
        dup = dup_result.scalars().first()
        if dup:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Department with code '{dept_in.code}' already exists."
            )

    # Verify head employee exists if head_employee_id is changing
    if dept_in.head_employee_id is not None and dept_in.head_employee_id != dept.head_employee_id:
        head_result = await db.execute(select(Employee).filter(Employee.id == dept_in.head_employee_id))
        head = head_result.scalars().first()
        if not head:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Head employee with ID {dept_in.head_employee_id} does not exist."
            )

    # Verify parent department loops
    if dept_in.parent_department_id is not None:
        if dept_in.parent_department_id == id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A department cannot be its own parent."
            )
        
        # Verify parent department exists
        parent_result = await db.execute(select(Department).filter(Department.id == dept_in.parent_department_id))
        parent = parent_result.scalars().first()
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Parent department with ID {dept_in.parent_department_id} does not exist."
            )

        # Verify circular loop
        if await is_ancestor(db, dept_in.parent_department_id, id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Circular department hierarchy detected: The target parent department is a child of this department."
            )

    # Apply updates
    update_data = dept_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(dept, key, value)

    await db.commit()
    res = await db.execute(
        select(Department)
        .options(selectinload(Department.head_employee), selectinload(Department.parent_department))
        .filter(Department.id == id)
    )
    return res.scalars().first()

@router.delete("/{id}", response_model=DepartmentRead)
async def delete_department(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(require_role("Admin"))
):
    result = await db.execute(select(Department).filter(Department.id == id))
    dept = result.scalars().first()
    if not dept:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Department with ID {id} not found."
        )

    # Perform soft-deactivation
    dept.status = StatusEnum.INACTIVE
    await db.commit()
    res = await db.execute(
        select(Department)
        .options(selectinload(Department.head_employee), selectinload(Department.parent_department))
        .filter(Department.id == id)
    )
    return res.scalars().first()
