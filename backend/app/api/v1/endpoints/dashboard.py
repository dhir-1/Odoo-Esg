from datetime import date, timedelta, datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, extract
from sqlalchemy.orm import selectinload

from app.db.database import get_db
from app.models.employee import Employee
from app.models.department import Department, DepartmentScore
from app.models.carbon import CarbonTransaction
from app.models.activity_log import ActivityLog
from app.models.enums import StatusEnum, RoleEnum
from app.core.permissions import get_current_user, require_role
from app.services.reports import get_allowed_department_ids
from app.services.scoring import calculate_org_score
from app.schemas.dashboard import (
    DashboardSummary,
    EmissionsTrendPoint,
    DepartmentRank,
    DashboardActivityLog
)

router = APIRouter()


@router.get("/summary", response_model=DashboardSummary, summary="Get Dashboard Summary KPI Metrics")
async def get_dashboard_summary(
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    """
    Returns the four primary KPI values (E, S, G, and Overall ESG scores).
    - Managers/Employees: Scoped to their own department's latest scores.
    - Admins: Returns organization-wide employee-count weighted average scores.
    """
    # 1. Admin Organization-Wide Aggregations
    if current_user.role == RoleEnum.ADMIN:
        # Determine the latest calculation period from the database
        latest_calc_stmt = select(DepartmentScore).order_by(DepartmentScore.calculated_at.desc()).limit(1)
        latest_calc_res = await db.execute(latest_calc_stmt)
        latest_calc = latest_calc_res.scalars().first()
        
        if not latest_calc:
            return DashboardSummary(
                environmental_score=0.0,
                social_score=0.0,
                governance_score=0.0,
                overall_esg_score=0.0
            )
            
        org_scores = await calculate_org_score(db, latest_calc.period_start, latest_calc.period_end)
        return DashboardSummary(
            environmental_score=org_scores["environmental_avg"],
            social_score=org_scores["social_avg"],
            governance_score=org_scores["governance_avg"],
            overall_esg_score=org_scores["total_score"]
        )

    # 2. Manager / Employee Scoped Calculations
    dept_id = current_user.department_id
    stmt = (
        select(DepartmentScore)
        .filter(DepartmentScore.department_id == dept_id)
        .order_by(DepartmentScore.calculated_at.desc())
        .limit(1)
    )
    res = await db.execute(stmt)
    score = res.scalars().first()
    
    if not score:
        return DashboardSummary(
            environmental_score=0.0,
            social_score=0.0,
            governance_score=0.0,
            overall_esg_score=0.0
        )
        
    return DashboardSummary(
        environmental_score=float(score.environmental_score),
        social_score=float(score.social_score),
        governance_score=float(score.governance_score),
        overall_esg_score=float(score.total_score)
    )


@router.get("/emissions-trend", response_model=List[EmissionsTrendPoint], summary="Get Monthly Emissions Trend")
async def get_emissions_trend(
    months: int = Query(12, ge=1, le=24, description="Trailing month history limit"),
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    """
    Returns monthly carbon emissions total (CO2e) over the trailing N months.
    - Managers/Employees: Scoped strictly to their own department.
    - Admins: Aggregated organization-wide.
    """
    # 1. Resolve Start Date (First day of month, N months ago)
    today = date.today()
    # Go back N months and align to the 1st of that month
    start_year = today.year
    start_month = today.month - months + 1
    while start_month <= 0:
        start_month += 12
        start_year -= 1
    start_date = date(start_year, start_month, 1)

    # 2. Query aggregated monthly emissions
    query = (
        select(
            extract('year', CarbonTransaction.transaction_date).label('year'),
            extract('month', CarbonTransaction.transaction_date).label('month'),
            func.coalesce(func.sum(CarbonTransaction.calculated_co2e), 0.0).label('total_co2e')
        )
        .filter(CarbonTransaction.transaction_date >= start_date)
    )

    if current_user.role != RoleEnum.ADMIN:
        query = query.filter(CarbonTransaction.department_id == current_user.department_id)

    query = query.group_by('year', 'month').order_by('year', 'month')
    res = await db.execute(query)

    # Map raw rows
    db_points = {}
    for r in res.all():
        yr = int(r[0])
        mn = int(r[1])
        co2e = float(r[2])
        db_points[f"{yr:04d}-{mn:02d}"] = co2e

    # 3. Fill in all intervals chronologically to ensure seamless charts
    trend = []
    curr_yr, curr_mn = start_year, start_month
    for _ in range(months):
        p_key = f"{curr_yr:04d}-{curr_mn:02d}"
        trend.append(EmissionsTrendPoint(
            period=p_key,
            co2e=round(db_points.get(p_key, 0.0), 2)
        ))
        
        curr_mn += 1
        if curr_mn > 12:
            curr_mn = 1
            curr_yr += 1

    return trend


@router.get("/department-ranking", response_model=List[DepartmentRank], summary="Get Department Performance Rankings")
async def get_department_ranking(
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(require_role("Admin"))
):
    """
    Returns rankings of all active departments by total score (descending).
    Only accessible to Administrators (Managers querying this receive a 403 Forbidden error).
    """
    # Subquery to identify the latest calculated_at for each department score
    latest_calc_sub = (
        select(
            DepartmentScore.department_id,
            func.max(DepartmentScore.calculated_at).label('max_calc')
        )
        .group_by(DepartmentScore.department_id)
        .subquery()
    )

    query = (
        select(
            Department.id,
            Department.name,
            DepartmentScore.total_score,
            DepartmentScore.environmental_score,
            DepartmentScore.social_score,
            DepartmentScore.governance_score
        )
        .join(DepartmentScore, DepartmentScore.department_id == Department.id)
        .join(
            latest_calc_sub,
            and_(
                DepartmentScore.department_id == latest_calc_sub.c.department_id,
                DepartmentScore.calculated_at == latest_calc_sub.c.max_calc
            )
        )
        .filter(Department.status == StatusEnum.ACTIVE)
        .order_by(DepartmentScore.total_score.desc())
    )

    res = await db.execute(query)
    ranking = []
    for row in res.all():
        ranking.append(DepartmentRank(
            department_id=row[0],
            department_name=row[1],
            total_score=float(row[2]),
            environmental_score=float(row[3]),
            social_score=float(row[4]),
            governance_score=float(row[5])
        ))

    return ranking


@router.get("/recent-activity", response_model=List[DashboardActivityLog], summary="Get Dashboard Activity Feed")
async def get_recent_activity(
    limit: int = Query(10, ge=1, le=50, description="Activity feed limit size"),
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    """
    Returns the feed of recent ESG actions.
    - Managers: Scoped to their nested sub-departments or org-wide events.
    - Admins: Full organization-wide view.
    """
    if current_user.role == RoleEnum.ADMIN:
        query = (
            select(ActivityLog)
            .options(selectinload(ActivityLog.actor))
            .order_by(ActivityLog.created_at.desc())
        )
    else:
        allowed_ids = await get_allowed_department_ids(db, current_user)
        query = (
            select(ActivityLog)
            .options(selectinload(ActivityLog.actor))
            .filter(
                or_(
                    ActivityLog.department_id.in_(allowed_ids),
                    ActivityLog.department_id == None
                )
            )
            .order_by(ActivityLog.created_at.desc())
        )

    query = query.limit(limit)
    res = await db.execute(query)
    logs = res.scalars().all()

    output = []
    for log in logs:
        output.append(DashboardActivityLog(
            id=log.id,
            event_type=log.event_type.value,
            actor_employee_id=log.actor_employee_id,
            actor_name=log.actor.full_name if log.actor else None,
            department_id=log.department_id,
            summary_text=log.summary_text,
            related_entity_type=log.related_entity_type,
            related_entity_id=log.related_entity_id,
            created_at=log.created_at
        ))

    return output
