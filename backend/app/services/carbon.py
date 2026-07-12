from typing import Optional
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.carbon import CarbonTransaction
from app.models.environmental import EmissionFactor
from app.models.enums import CarbonSourceModuleEnum, ActivityLogEventTypeEnum
from app.services.activity_log import log_activity

async def calculate_and_log_emission(
    db: AsyncSession,
    source_module: CarbonSourceModuleEnum,
    source_reference_id: Optional[str],
    department_id: int,
    quantity: float,
    emission_factor_id: int,
    created_by_id: int,
    notes: Optional[str] = None
) -> CarbonTransaction:
    """
    Service helper to calculate CO2e emissions using raw quantity and conversion factors.
    Inserts a CarbonTransaction, flushes the transaction, and logs the public activity log.
    """
    # Fetch emission factor
    result = await db.execute(select(EmissionFactor).filter(EmissionFactor.id == emission_factor_id))
    ef = result.scalars().first()
    if not ef:
        raise ValueError(f"Emission factor with ID {emission_factor_id} not found.")

    # Calculate co2e
    calculated_co2e = float(quantity) * float(ef.co2e_per_unit)

    # Insert transaction
    new_tx = CarbonTransaction(
        department_id=department_id,
        source_module=source_module,
        source_reference_id=source_reference_id,
        emission_factor_id=emission_factor_id,
        quantity=quantity,
        calculated_co2e=calculated_co2e,
        transaction_date=date.today(), # Set to current date
        is_auto_calculated=True,
        created_by_id=created_by_id,
        notes=notes
    )
    
    # Wait, we need to import date from datetime
    db.add(new_tx)
    await db.flush() # Populate new_tx.id

    # Log to public ActivityLog
    summary = f"Carbon Transaction Logged: {calculated_co2e:.2f} kg CO2e ({source_module.value})"
    await log_activity(
        db=db,
        event_type=ActivityLogEventTypeEnum.CARBON_TRANSACTION_LOGGED,
        actor_employee_id=created_by_id,
        department_id=department_id,
        summary_text=summary,
        related_entity_type="CarbonTransaction",
        related_entity_id=new_tx.id
    )

    return new_tx
