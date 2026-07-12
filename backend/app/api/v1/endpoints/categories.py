from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import get_db
from app.models.category import Category
from app.models.employee import Employee
from app.models.enums import StatusEnum, CategoryTypeEnum
from app.core.permissions import get_current_user, require_role
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryRead

router = APIRouter()

@router.post("/", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_in: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(require_role("Admin"))
):
    new_category = Category(
        name=category_in.name,
        type=category_in.type,
        status=StatusEnum.ACTIVE
    )
    db.add(new_category)
    await db.commit()
    await db.refresh(new_category)
    return new_category

@router.get("/", response_model=List[CategoryRead])
async def list_categories(
    type: Optional[CategoryTypeEnum] = Query(None),
    status: Optional[StatusEnum] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    query = select(Category)
    if type:
        query = query.filter(Category.type == type)
    if status:
        query = query.filter(Category.status == status)

    query = query.offset(offset).limit(limit).order_by(Category.id)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{id}", response_model=CategoryRead)
async def get_category(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    result = await db.execute(select(Category).filter(Category.id == id))
    category = result.scalars().first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with ID {id} not found."
        )
    return category

@router.patch("/{id}", response_model=CategoryRead)
async def update_category(
    id: int,
    category_in: CategoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(require_role("Admin"))
):
    result = await db.execute(select(Category).filter(Category.id == id))
    category = result.scalars().first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with ID {id} not found."
        )

    update_data = category_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(category, key, value)

    await db.commit()
    await db.refresh(category)
    return category

@router.delete("/{id}", response_model=CategoryRead)
async def delete_category(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(require_role("Admin"))
):
    result = await db.execute(select(Category).filter(Category.id == id))
    category = result.scalars().first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with ID {id} not found."
        )

    # Soft delete
    category.status = StatusEnum.INACTIVE
    await db.commit()
    await db.refresh(category)
    return category
