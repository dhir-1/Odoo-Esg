import logging
from typing import Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.notification import Notification
from app.models.enums import NotificationTypeEnum, PolicyStatusEnum, StatusEnum
from app.models.governance import ESGPolicy, PolicyAcknowledgement
from app.models.employee import Employee
from app.services.settings import get_esg_config
from app.websockets.manager import ws_manager

logger = logging.getLogger(__name__)

async def create_notification(
    db: AsyncSession,
    recipient_id: int,
    type: NotificationTypeEnum,
    title: str,
    message: str,
    related_entity_type: Optional[str] = None,
    related_entity_id: Optional[int] = None,
) -> Optional[Notification]:
    """
    Central notification creation helper.
    Respects the ESGConfiguration toggles (notify_on_*).
    Saves the notification to the database (flushes to populate defaults/id)
    and broadcasts to WebSocket connections if the recipient is connected.
    """
    config = await get_esg_config(db)

    # Respect the relevant toggle
    enabled = True
    if type == NotificationTypeEnum.COMPLIANCE_ISSUE:
        enabled = config.notify_on_compliance_issue
    elif type == NotificationTypeEnum.APPROVAL_DECISION:
        enabled = config.notify_on_approval_decision
    elif type == NotificationTypeEnum.POLICY_REMINDER:
        enabled = config.notify_on_policy_reminder
    elif type == NotificationTypeEnum.BADGE_UNLOCK:
        enabled = config.notify_on_badge_unlock

    if not enabled:
        logger.info(f"Notification of type {type.value} is disabled in ESGConfiguration. Skipping.")
        return None

    notification = Notification(
        recipient_id=recipient_id,
        type=type,
        title=title,
        message=message,
        is_read=False,
        related_entity_type=related_entity_type,
        related_entity_id=related_entity_id
    )
    db.add(notification)
    await db.flush()  # Populates id and created_at

    # Broadcast via WebSocket
    payload = {
        "event": "new_notification",
        "data": {
            "id": notification.id,
            "type": notification.type.value,
            "title": notification.title,
            "message": notification.message,
            "is_read": notification.is_read,
            "related_entity_type": notification.related_entity_type,
            "related_entity_id": notification.related_entity_id,
            "created_at": notification.created_at.isoformat() if notification.created_at else datetime.now(timezone.utc).isoformat()
        }
    }
    await ws_manager.broadcast_to_employee(recipient_id, payload)
    
    return notification


async def run_policy_acknowledgement_reminders(db: AsyncSession):
    """
    Scheduled job that checks for active ESGPolicy records requiring acknowledgement,
    finds active employees who haven't acknowledged the current version,
    and sends a policy_reminder notification.
    Ensures no employee receives more than one reminder per policy per 7 days.
    """
    logger.info("⏰ Starting scheduled policy acknowledgement reminders check...")

    # Get active policies requiring acknowledgement
    policies_res = await db.execute(
        select(ESGPolicy)
        .filter(
            ESGPolicy.status == PolicyStatusEnum.ACTIVE,
            ESGPolicy.requires_acknowledgement == True
        )
    )
    policies = policies_res.scalars().all()
    if not policies:
        logger.info("No active policies requiring acknowledgement found.")
        return

    # Get all active employees
    employees_res = await db.execute(
        select(Employee)
        .filter(Employee.status == StatusEnum.ACTIVE)
    )
    employees = employees_res.scalars().all()
    if not employees:
        logger.info("No active employees found.")
        return

    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    reminders_sent = 0

    for policy in policies:
        for employee in employees:
            # Check if employee has acknowledged the current version
            ack_res = await db.execute(
                select(PolicyAcknowledgement)
                .filter(
                    PolicyAcknowledgement.employee_id == employee.id,
                    PolicyAcknowledgement.policy_id == policy.id,
                    PolicyAcknowledgement.policy_version == policy.version
                )
            )
            has_acknowledged = ack_res.scalars().first() is not None

            if not has_acknowledged:
                # Check if reminded in the last 7 days (look up Notification table)
                notif_res = await db.execute(
                    select(Notification)
                    .filter(
                        Notification.recipient_id == employee.id,
                        Notification.type == NotificationTypeEnum.POLICY_REMINDER,
                        Notification.related_entity_type == "ESGPolicy",
                        Notification.related_entity_id == policy.id,
                        Notification.created_at >= seven_days_ago
                    )
                )
                already_reminded = notif_res.scalars().first() is not None

                if not already_reminded:
                    await create_notification(
                        db=db,
                        recipient_id=employee.id,
                        type=NotificationTypeEnum.POLICY_REMINDER,
                        title="Policy Acknowledgement Required",
                        message=f"Please review and acknowledge policy: '{policy.title}' (version {policy.version}).",
                        related_entity_type="ESGPolicy",
                        related_entity_id=policy.id
                    )
                    reminders_sent += 1

    # Commit any changes (reminders created) in the batch session
    if reminders_sent > 0:
        await db.commit()

    logger.info(f"✅ Policy acknowledgement reminders run complete. Sent {reminders_sent} reminder(s).")
