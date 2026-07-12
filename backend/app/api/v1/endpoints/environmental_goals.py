from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import get_db
from app.models.environmental import EnvironmentalGoal
from app.models.department import Department
from app.models.employee import Employee
from app.models.enums import RoleEnum, GoalLifecycleStatusEnum
from app.core.permissions import get_current_user, require_role, has_department_access
from app.schemas.environmental import EnvironmentalGoalCreate, EnvironmentalGoalUpdate, EnvironmentalGoalRead

router = APIRouter()

@router.post("/", response_model=EnvironmentalGoalRead, status_code=status.HTTP_201_CREATED)
async def create_environmental_goal(
    goal_in: EnvironmentalGoalCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(require_role("Admin", "Manager"))
):
    # Manager scope checks
    if current_user.role == RoleEnum.MANAGER:
        if goal_in.department_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Managers cannot create company-wide environmental goals."
            )
        if not await has_department_access(db, current_user, goal_in.department_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to create environmental goals for this department."
            )

    # Verify department exists if provided
    if goal_in.department_id is not None:
        dept_res = await db.execute(select(Department).filter(Department.id == goal_in.department_id))
        if not dept_res.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Department with ID {goal_in.department_id} not found."
            )

    new_goal = EnvironmentalGoal(
        title=goal_in.title,
        description=goal_in.description,
        department_id=goal_in.department_id,
        metric_type=goal_in.metric_type,
        target_value=goal_in.target_value,
        current_value=goal_in.current_value,
        unit=goal_in.unit,
        start_date=goal_in.start_date,
        target_date=goal_in.target_date,
        lifecycle_status=GoalLifecycleStatusEnum.ACTIVE
    )
    db.add(new_goal)
    await db.commit()
    await db.refresh(new_goal)
    return new_goal

@router.get("/", response_model=List[EnvironmentalGoalRead])
async def list_environmental_goals(
    department_id: Optional[int] = Query(None),
    lifecycle_status: Optional[GoalLifecycleStatusEnum] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    query = select(EnvironmentalGoal)
    if department_id is not None:
        query = query.filter(EnvironmentalGoal.department_id == department_id)
    if lifecycle_status:
        query = query.filter(EnvironmentalGoal.lifecycle_status == lifecycle_status)

    query = query.offset(offset).limit(limit).order_by(EnvironmentalGoal.id)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{id}", response_model=EnvironmentalGoalRead)
async def get_environmental_goal(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    result = await db.execute(select(EnvironmentalGoal).filter(EnvironmentalGoal.id == id))
    goal = result.scalars().first()
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Environmental Goal with ID {id} not found."
        )
    return goal

@router.patch("/{id}", response_model=EnvironmentalGoalRead)
async def update_environmental_goal(
    id: int,
    goal_in: EnvironmentalGoalUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(require_role("Admin", "Manager"))
):
    result = await db.execute(select(EnvironmentalGoal).filter(EnvironmentalGoal.id == id))
    goal = result.scalars().first()
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Environmental Goal with ID {id} not found."
        )

    # Manager scope checking
    if current_user.role == RoleEnum.MANAGER:
        if goal.department_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Managers cannot modify company-wide environmental goals."
            )
        if not await has_department_access(db, current_user, goal.department_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Environmental goal does not belong to your department hierarchy."
            )
        if goal_in.department_id is not None and goal_in.department_id != goal.department_id:
            if not await has_department_access(db, current_user, goal_in.department_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: Cannot reassign environmental goal to a department outside your hierarchy."
                )

    # Verify department exists if provided
    if goal_in.department_id is not None:
        dept_res = await db.execute(select(Department).filter(Department.id == goal_in.department_id))
        if not dept_res.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Department with ID {goal_in.department_id} not found."
            )

    update_data = goal_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(goal, key, value)

    await db.commit()
    await db.refresh(goal)
    return goal

@router.delete("/{id}", response_model=EnvironmentalGoalRead)
async def delete_environmental_goal(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(require_role("Admin", "Manager"))
):
    result = await db.execute(select(EnvironmentalGoal).filter(EnvironmentalGoal.id == id))
    goal = result.scalars().first()
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Environmental Goal with ID {id} not found."
        )

    # Manager scope checking
    if current_user.role == RoleEnum.MANAGER:
        if goal.department_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Managers cannot cancel company-wide environmental goals."
            )
        if not await has_department_access(db, current_user, goal.department_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Environmental goal does not belong to your department hierarchy."
            )

    # Soft delete: CANCELLED lifecycle status
    goal.lifecycle_status = GoalLifecycleStatusEnum.CANCELLED
    await db.commit()
    await db.refresh(goal)
    return goal
