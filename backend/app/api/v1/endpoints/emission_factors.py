from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import get_db
from app.models.environmental import EmissionFactor
from app.models.category import Category
from app.models.employee import Employee
from app.models.enums import StatusEnum, EmissionActivityTypeEnum
from app.core.permissions import get_current_user, require_role
from app.schemas.environmental import EmissionFactorCreate, EmissionFactorUpdate, EmissionFactorRead

router = APIRouter()

@router.post("/", response_model=EmissionFactorRead, status_code=status.HTTP_201_CREATED)
async def create_emission_factor(
    ef_in: EmissionFactorCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(require_role("Admin"))
):
    # Verify category if provided
    if ef_in.category_id is not None:
        cat_res = await db.execute(select(Category).filter(Category.id == ef_in.category_id))
        if not cat_res.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category with ID {ef_in.category_id} not found."
            )

    new_ef = EmissionFactor(
        name=ef_in.name,
        activity_type=ef_in.activity_type,
        unit=ef_in.unit,
        co2e_per_unit=ef_in.co2e_per_unit,
        category_id=ef_in.category_id,
        source_reference=ef_in.source_reference,
        effective_from=ef_in.effective_from,
        effective_to=ef_in.effective_to,
        status=StatusEnum.ACTIVE
    )
    db.add(new_ef)
    await db.commit()
    await db.refresh(new_ef)
    return new_ef

@router.get("/", response_model=List[EmissionFactorRead])
async def list_emission_factors(
    activity_type: Optional[EmissionActivityTypeEnum] = Query(None),
    status: Optional[StatusEnum] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    query = select(EmissionFactor)
    if activity_type:
        query = query.filter(EmissionFactor.activity_type == activity_type)
    if status:
        query = query.filter(EmissionFactor.status == status)

    query = query.offset(offset).limit(limit).order_by(EmissionFactor.id)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{id}", response_model=EmissionFactorRead)
async def get_emission_factor(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    result = await db.execute(select(EmissionFactor).filter(EmissionFactor.id == id))
    ef = result.scalars().first()
    if not ef:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Emission Factor with ID {id} not found."
        )
    return ef

@router.patch("/{id}", response_model=EmissionFactorRead)
async def update_emission_factor(
    id: int,
    ef_in: EmissionFactorUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(require_role("Admin"))
):
    result = await db.execute(select(EmissionFactor).filter(EmissionFactor.id == id))
    ef = result.scalars().first()
    if not ef:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Emission Factor with ID {id} not found."
        )

    # Verify category if provided
    if ef_in.category_id is not None:
        cat_res = await db.execute(select(Category).filter(Category.id == ef_in.category_id))
        if not cat_res.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category with ID {ef_in.category_id} not found."
            )

    update_data = ef_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(ef, key, value)

    await db.commit()
    await db.refresh(ef)
    return ef

@router.delete("/{id}", response_model=EmissionFactorRead)
async def delete_emission_factor(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(require_role("Admin"))
):
    result = await db.execute(select(EmissionFactor).filter(EmissionFactor.id == id))
    ef = result.scalars().first()
    if not ef:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Emission Factor with ID {id} not found."
        )

    # Soft delete
    ef.status = StatusEnum.INACTIVE
    await db.commit()
    await db.refresh(ef)
    return ef
