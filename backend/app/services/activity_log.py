from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.activity_log import ActivityLog
from app.models.enums import ActivityLogEventTypeEnum

async def log_activity(
    db: AsyncSession,
    event_type: ActivityLogEventTypeEnum,
    actor_employee_id: Optional[int],
    department_id: Optional[int],
    summary_text: str,
    related_entity_type: Optional[str] = None,
    related_entity_id: Optional[int] = None
) -> ActivityLog:
    """
    Central utility to log organization-wide activities.
    This helper flushes changes to the session so the object gets populated (e.g. gets an ID),
    but leaves the commit to the transaction manager/route handler.
    """
    log_entry = ActivityLog(
        event_type=event_type,
        actor_employee_id=actor_employee_id,
        department_id=department_id,
        summary_text=summary_text,
        related_entity_type=related_entity_type,
        related_entity_id=related_entity_id
    )
    db.add(log_entry)
    await db.flush()
    return log_entry
