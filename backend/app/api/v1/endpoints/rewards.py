from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import get_db
from app.models.gamification import Reward
from app.models.employee import Employee
from app.models.enums import StatusEnum
from app.core.permissions import get_current_user, require_role
from app.schemas.gamification import RewardCreate, RewardUpdate, RewardRead

router = APIRouter()

@router.post("/", response_model=RewardRead, status_code=status.HTTP_201_CREATED)
async def create_reward(
    reward_in: RewardCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(require_role("Admin"))
):
    new_reward = Reward(
        name=reward_in.name,
        description=reward_in.description,
        points_required=reward_in.points_required,
        stock=reward_in.stock,
        status=StatusEnum.ACTIVE
    )
    db.add(new_reward)
    await db.commit()
    await db.refresh(new_reward)
    return new_reward

@router.get("/", response_model=List[RewardRead])
async def list_rewards(
    status: Optional[StatusEnum] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    query = select(Reward)
    if status:
        query = query.filter(Reward.status == status)

    query = query.offset(offset).limit(limit).order_by(Reward.id)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{id}", response_model=RewardRead)
async def get_reward(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    result = await db.execute(select(Reward).filter(Reward.id == id))
    reward = result.scalars().first()
    if not reward:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reward with ID {id} not found."
        )
    return reward

@router.patch("/{id}", response_model=RewardRead)
async def update_reward(
    id: int,
    reward_in: RewardUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(require_role("Admin"))
):
    result = await db.execute(select(Reward).filter(Reward.id == id))
    reward = result.scalars().first()
    if not reward:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reward with ID {id} not found."
        )

    update_data = reward_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(reward, key, value)

    await db.commit()
    await db.refresh(reward)
    return reward

@router.delete("/{id}", response_model=RewardRead)
async def delete_reward(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(require_role("Admin"))
):
    result = await db.execute(select(Reward).filter(Reward.id == id))
    reward = result.scalars().first()
    if not reward:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reward with ID {id} not found."
        )

    # Soft delete
    reward.status = StatusEnum.INACTIVE
    await db.commit()
    await db.refresh(reward)
    return reward
