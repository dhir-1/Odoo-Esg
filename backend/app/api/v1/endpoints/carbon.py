from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.database import get_db
from app.models.carbon import CarbonTransaction
from app.models.department import Department
from app.models.employee import Employee
from app.models.environmental import EmissionFactor
from app.models.enums import CarbonSourceModuleEnum, ActivityLogEventTypeEnum
from app.core.permissions import get_current_user, require_role
from app.schemas.carbon import (
    CarbonTransactionCreate,
    CarbonTransactionSimulate,
    CarbonTransactionRead,
    DepartmentCarbonSummary
)
from app.services.settings import get_esg_config
from app.services.carbon import calculate_and_log_emission
from app.services.activity_log import log_activity

router = APIRouter()

@router.post("/", response_model=CarbonTransactionRead, status_code=status.HTTP_201_CREATED)
async def create_manual_transaction(
    tx_in: CarbonTransactionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(require_role("Admin", "Manager"))
):
    # Verify department exists
    dept_result = await db.execute(select(Department).filter(Department.id == tx_in.department_id))
    if not dept_result.scalars().first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Department with ID {tx_in.department_id} not found.")

    # Verify emission factor exists
    ef_result = await db.execute(select(EmissionFactor).filter(EmissionFactor.id == tx_in.emission_factor_id))
    if not ef_result.scalars().first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Emission Factor with ID {tx_in.emission_factor_id} not found.")

    new_tx = CarbonTransaction(
        department_id=tx_in.department_id,
        source_module=CarbonSourceModuleEnum.MANUAL,
        source_reference_id=None,
        emission_factor_id=tx_in.emission_factor_id,
        quantity=tx_in.quantity,
        calculated_co2e=tx_in.calculated_co2e,
        transaction_date=tx_in.transaction_date,
        is_auto_calculated=False,
        created_by_id=current_user.id,
        notes=tx_in.notes
    )

    db.add(new_tx)
    await db.flush()

    # Log to public ActivityLog
    summary = f"Carbon Transaction Logged: {tx_in.calculated_co2e:.2f} kg CO2e (Manual)"
    await log_activity(
        db=db,
        event_type=ActivityLogEventTypeEnum.CARBON_TRANSACTION_LOGGED,
        actor_employee_id=current_user.id,
        department_id=tx_in.department_id,
        summary_text=summary,
        related_entity_type="CarbonTransaction",
        related_entity_id=new_tx.id
    )

    await db.commit()
    await db.refresh(new_tx)
    return new_tx

@router.post("/simulate", response_model=CarbonTransactionRead, status_code=status.HTTP_201_CREATED)
async def simulate_transaction(
    tx_in: CarbonTransactionSimulate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(require_role("Admin", "Manager"))
):
    # Verify auto emission configuration toggle
    config = await get_esg_config(db)
    if not config.auto_emission_calculation_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Automated emission calculation is disabled in settings."
        )

    # Verify department exists
    dept_result = await db.execute(select(Department).filter(Department.id == tx_in.department_id))
    if not dept_result.scalars().first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Department with ID {tx_in.department_id} not found.")

    try:
        new_tx = await calculate_and_log_emission(
            db=db,
            source_module=tx_in.source_module,
            source_reference_id=tx_in.source_reference_id,
            department_id=tx_in.department_id,
            quantity=tx_in.quantity,
            emission_factor_id=tx_in.emission_factor_id,
            created_by_id=current_user.id,
            notes=tx_in.notes
        )
        await db.commit()
        await db.refresh(new_tx)
        return new_tx
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/", response_model=List[CarbonTransactionRead])
async def list_transactions(
    start_date: Optional[date] = Query(None, description="Start date filter"),
    end_date: Optional[date] = Query(None, description="End date filter"),
    department_id: Optional[int] = Query(None, description="Filter by department ID"),
    limit: int = Query(10, ge=1, le=100, description="Page limit size"),
    offset: int = Query(0, ge=0, description="Offset count"),
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    query = select(CarbonTransaction)
    if start_date:
        query = query.filter(CarbonTransaction.transaction_date >= start_date)
    if end_date:
        query = query.filter(CarbonTransaction.transaction_date <= end_date)
    if department_id:
        query = query.filter(CarbonTransaction.department_id == department_id)
        
    query = query.offset(offset).limit(limit).order_by(CarbonTransaction.id.desc())
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/department-totals", response_model=List[DepartmentCarbonSummary])
async def department_totals(
    start_date: Optional[date] = Query(None, description="Start date filter"),
    end_date: Optional[date] = Query(None, description="End date filter"),
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    # Perform grouping query joining departments
    # Aggregate sums, fallback to 0 if null
    query = (
        select(
            Department.id.label("department_id"),
            Department.name.label("department_name"),
            func.coalesce(func.sum(CarbonTransaction.calculated_co2e), 0.0).label("total_co2e")
        )
        .join(CarbonTransaction, CarbonTransaction.department_id == Department.id, isouter=True)
    )

    if start_date:
        query = query.filter(CarbonTransaction.transaction_date >= start_date)
    if end_date:
        query = query.filter(CarbonTransaction.transaction_date <= end_date)

    query = query.group_by(Department.id, Department.name).order_by(Department.id)
    
    result = await db.execute(query)
    # Output structure will match DepartmentCarbonSummary schema
    summaries = []
    for row in result.fetchall():
        summaries.append({
            "department_id": row[0],
            "department_name": row[1],
            "total_co2e": float(row[2])
        })
    return summaries
