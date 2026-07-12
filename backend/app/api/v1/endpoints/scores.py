from datetime import date, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.models.employee import Employee
from app.models.department import Department, DepartmentScore
from app.models.enums import StatusEnum
from app.core.permissions import get_current_user, require_role, has_department_access
from app.schemas.scoring import DepartmentScoreRead, OrgScoreSummary, ScoreCalculationResponse
from app.services.scoring import (
    calculate_department_score,
    calculate_org_score,
)

router = APIRouter()


@router.post(
    "/calculate",
    response_model=ScoreCalculationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Trigger ESG score calculation for a department",
)
async def trigger_score_calculation(
    department_id: int = Query(..., description="Department ID to calculate score for"),
    period_start: date = Query(..., description="Start of scoring period (YYYY-MM-DD)"),
    period_end: date = Query(..., description="End of scoring period (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(require_role("Admin", "Manager")),
):
    """
    Triggers an on-demand ESG score recalculation for the specified department
    and period.  Admin can calculate for any department; Manager is restricted
    to their own department sub-tree.
    """
    # Validate period
    if period_end < period_start:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="period_end must be on or after period_start.",
        )

    # Validate department exists
    dept_result = await db.execute(
        select(Department).filter(Department.id == department_id)
    )
    dept = dept_result.scalars().first()
    if not dept:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Department with ID {department_id} not found.",
        )

    # Manager RBAC: restrict to own department tree
    if current_user.role.value == "Manager":
        has_access = await has_department_access(db, current_user, department_id)
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Managers can only calculate scores for their own department sub-tree.",
            )

    score = await calculate_department_score(db, department_id, period_start, period_end)

    return ScoreCalculationResponse(
        message=f"ESG score calculated for department '{dept.name}' ({period_start} to {period_end}).",
        score=DepartmentScoreRead.model_validate(score),
    )


@router.get(
    "/department/{id}/history",
    response_model=List[DepartmentScoreRead],
    summary="Get ESG score history for a department",
)
async def get_department_score_history(
    id: int,
    limit: int = Query(20, ge=1, le=100, description="Max results to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    """
    Returns paginated history of DepartmentScore rows for a given department,
    ordered by calculated_at descending (most recent first).
    """
    # Validate department exists
    dept_result = await db.execute(
        select(Department).filter(Department.id == id)
    )
    if not dept_result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Department with ID {id} not found.",
        )

    query = (
        select(DepartmentScore)
        .filter(DepartmentScore.department_id == id)
        .order_by(DepartmentScore.calculated_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(query)
    return result.scalars().all()


@router.get(
    "/org-summary",
    response_model=OrgScoreSummary,
    summary="Get organisation-wide ESG score summary",
)
async def get_org_score_summary(
    period_start: Optional[date] = Query(
        None,
        description="Start of period. Defaults to 30 days ago if omitted.",
    ),
    period_end: Optional[date] = Query(
        None,
        description="End of period. Defaults to today if omitted.",
    ),
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    """
    Returns the employee-count-weighted average ESG score across all departments
    for the specified (or default trailing-30-day) period.
    """
    if period_end is None:
        period_end = date.today()
    if period_start is None:
        period_start = period_end - timedelta(days=30)

    if period_end < period_start:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="period_end must be on or after period_start.",
        )

    summary = await calculate_org_score(db, period_start, period_end)
    return summary
