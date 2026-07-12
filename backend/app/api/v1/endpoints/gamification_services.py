from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.db.database import get_db
from app.models.employee import Employee
from app.models.gamification import Badge, EmployeeBadge, Reward, RewardRedemption
from app.models.department import Department
from app.models.enums import StatusEnum
from app.core.permissions import get_current_user
from app.schemas.gamification import EmployeeBadgeRead, RewardRedemptionRead
from app.schemas.leaderboard import LeaderboardEntryRead

router = APIRouter()

@router.post("/rewards/{id}/redeem", response_model=RewardRedemptionRead, status_code=status.HTTP_201_CREATED)
async def redeem_reward(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    # Retrieve reward using row-level locking (FOR UPDATE)
    reward_res = await db.execute(
        select(Reward).filter(Reward.id == id).with_for_update()
    )
    reward = reward_res.scalars().first()
    if not reward:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reward with ID {id} not found."
        )

    # Retrieve employee using row-level locking (FOR UPDATE)
    employee_res = await db.execute(
        select(Employee).filter(Employee.id == current_user.id).with_for_update()
    )
    employee = employee_res.scalars().first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee profile not found."
        )

    # Validations
    if reward.status != StatusEnum.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This reward is currently inactive and cannot be redeemed."
        )

    if reward.stock <= 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Reward is out of stock."
        )

    if employee.points_balance < reward.points_required:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Insufficient points balance. Required: {reward.points_required}, Balance: {employee.points_balance}"
        )

    # Deduct stock and points balance
    reward.stock -= 1
    employee.points_balance -= reward.points_required

    # Create redemption log record
    redemption = RewardRedemption(
        employee_id=employee.id,
        reward_id=reward.id,
        points_spent=reward.points_required
    )
    db.add(redemption)

    # Commit changes inside locked transaction
    await db.commit()
    await db.refresh(redemption)
    
    # Load reward relationship manually to satisfy schema output
    redemption_res = await db.execute(
        select(RewardRedemption)
        .options(selectinload(RewardRedemption.reward))
        .filter(RewardRedemption.id == redemption.id)
    )
    return redemption_res.scalars().first()

@router.get("/employees/{id}/badges", response_model=List[EmployeeBadgeRead])
async def list_employee_badges(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    # Verify employee exists
    emp_res = await db.execute(select(Employee).filter(Employee.id == id))
    if not emp_res.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with ID {id} not found."
        )

    query = (
        select(EmployeeBadge)
        .options(selectinload(EmployeeBadge.badge))
        .filter(EmployeeBadge.employee_id == id)
        .order_by(EmployeeBadge.awarded_at.desc())
    )
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/leaderboard", response_model=List[LeaderboardEntryRead])
async def get_leaderboard(
    entry_type: str = Query("combined", regex="^(employee|department|combined)$"),
    department_id: Optional[int] = Query(None),
    metric: str = Query("xp_points", regex="^(xp_points|points_balance)$"),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    if entry_type == "employee":
        query = (
            select(Employee.id, Employee.full_name, getattr(Employee, metric).label("value"))
            .filter(Employee.status == StatusEnum.ACTIVE)
        )
        if department_id is not None:
            query = query.filter(Employee.department_id == department_id)
        query = query.order_by(getattr(Employee, metric).desc()).limit(limit)
        res = await db.execute(query)
        rows = res.all()
        return [
            {
                "rank": idx + 1,
                "entry_type": "employee",
                "id": r.id,
                "name": r.full_name,
                "value": int(r.value or 0)
            }
            for idx, r in enumerate(rows)
        ]

    elif entry_type == "department":
        query = (
            select(
                Department.id,
                Department.name,
                func.sum(getattr(Employee, metric)).label("value")
            )
            .join(Employee, Employee.department_id == Department.id)
            .filter(Department.status == StatusEnum.ACTIVE, Employee.status == StatusEnum.ACTIVE)
            .group_by(Department.id, Department.name)
            .order_by(func.sum(getattr(Employee, metric)).desc())
            .limit(limit)
        )
        res = await db.execute(query)
        rows = res.all()
        return [
            {
                "rank": idx + 1,
                "entry_type": "department",
                "id": r.id,
                "name": r.name,
                "value": int(r.value or 0)
            }
            for idx, r in enumerate(rows)
        ]

    else:  # combined
        # Fetch active employees
        emp_query = (
            select(Employee.id, Employee.full_name, getattr(Employee, metric).label("value"))
            .filter(Employee.status == StatusEnum.ACTIVE)
        )
        if department_id is not None:
            emp_query = emp_query.filter(Employee.department_id == department_id)
        emp_res = await db.execute(emp_query)
        emp_rows = emp_res.all()

        employees_list = [
            {
                "entry_type": "employee",
                "id": r.id,
                "name": r.full_name,
                "value": int(r.value or 0)
            }
            for r in emp_rows
        ]

        # Fetch active departments
        dept_query = (
            select(
                Department.id,
                Department.name,
                func.sum(getattr(Employee, metric)).label("value")
            )
            .join(Employee, Employee.department_id == Department.id)
            .filter(Department.status == StatusEnum.ACTIVE, Employee.status == StatusEnum.ACTIVE)
            .group_by(Department.id, Department.name)
        )
        dept_res = await db.execute(dept_query)
        dept_rows = dept_res.all()

        departments_list = [
            {
                "entry_type": "department",
                "id": r.id,
                "name": r.name,
                "value": int(r.value or 0)
            }
            for r in dept_rows
        ]

        combined = employees_list + departments_list
        # Sort descending by value
        combined.sort(key=lambda x: x["value"], reverse=True)

        # Build list with re-ranked entries
        results = []
        for idx, item in enumerate(combined):
            results.append({
                "rank": idx + 1,
                "entry_type": item["entry_type"],
                "id": item["id"],
                "name": item["name"],
                "value": item["value"]
            })
        return results[:limit]
