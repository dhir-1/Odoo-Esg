from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import get_db
from app.models.gamification import Badge
from app.models.employee import Employee
from app.core.permissions import get_current_user, require_role
from app.schemas.gamification import BadgeCreate, BadgeUpdate, BadgeRead

router = APIRouter()

@router.post("/", response_model=BadgeRead, status_code=status.HTTP_201_CREATED)
async def create_badge(
    badge_in: BadgeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(require_role("Admin"))
):
    new_badge = Badge(
        name=badge_in.name,
        description=badge_in.description,
        unlock_rule=badge_in.unlock_rule,
        icon_url=badge_in.icon_url
    )
    db.add(new_badge)
    await db.commit()
    await db.refresh(new_badge)
    return new_badge

@router.get("/", response_model=List[BadgeRead])
async def list_badges(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    query = select(Badge).offset(offset).limit(limit).order_by(Badge.id)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{id}", response_model=BadgeRead)
async def get_badge(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    result = await db.execute(select(Badge).filter(Badge.id == id))
    badge = result.scalars().first()
    if not badge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Badge with ID {id} not found."
        )
    return badge

@router.patch("/{id}", response_model=BadgeRead)
async def update_badge(
    id: int,
    badge_in: BadgeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(require_role("Admin"))
):
    result = await db.execute(select(Badge).filter(Badge.id == id))
    badge = result.scalars().first()
    if not badge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Badge with ID {id} not found."
        )

    update_data = badge_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(badge, key, value)

    await db.commit()
    await db.refresh(badge)
    return badge

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_badge(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(require_role("Admin"))
):
    result = await db.execute(select(Badge).filter(Badge.id == id))
    badge = result.scalars().first()
    if not badge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Badge with ID {id} not found."
        )

    await db.delete(badge)
    await db.commit()
    return
