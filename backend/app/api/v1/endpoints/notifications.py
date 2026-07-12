from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.db.database import get_db
from app.models.employee import Employee
from app.models.notification import Notification
from app.core.permissions import get_current_user
from app.schemas.notification import NotificationRead

router = APIRouter()

@router.get("", response_model=List[NotificationRead], summary="Get current employee's notifications")
async def list_notifications(
    is_read: Optional[bool] = Query(None, description="Filter by read/unread status"),
    limit: int = Query(20, ge=1, le=100, description="Pagination limit"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    """
    Returns current user's notifications, ordered by created_at descending.
    Can be filtered by is_read.
    """
    query = (
        select(Notification)
        .filter(Notification.recipient_id == current_user.id)
        .order_by(Notification.created_at.desc())
    )
    if is_read is not None:
        query = query.filter(Notification.is_read == is_read)

    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    return result.scalars().all()

@router.patch("/{id}/read", response_model=NotificationRead, summary="Mark notification as read")
async def mark_notification_as_read(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    """
    Marks a single notification belonging to the current user as read.
    """
    result = await db.execute(
        select(Notification)
        .filter(and_(Notification.id == id, Notification.recipient_id == current_user.id))
    )
    notification = result.scalars().first()
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification with ID {id} not found."
        )

    notification.is_read = True
    await db.commit()
    await db.refresh(notification)
    return notification
