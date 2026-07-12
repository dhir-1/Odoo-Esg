from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import get_db
from app.models.environmental import ProductESGProfile, EmissionFactor
from app.models.employee import Employee
from app.models.enums import StatusEnum
from app.core.permissions import get_current_user, require_role
from app.schemas.environmental import ProductESGProfileCreate, ProductESGProfileUpdate, ProductESGProfileRead

router = APIRouter()

@router.post("/", response_model=ProductESGProfileRead, status_code=status.HTTP_201_CREATED)
async def create_product_profile(
    profile_in: ProductESGProfileCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(require_role("Admin"))
):
    # Check duplicate SKU if provided
    if profile_in.sku is not None:
        sku_res = await db.execute(select(ProductESGProfile).filter(ProductESGProfile.sku == profile_in.sku))
        if sku_res.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product ESG Profile with SKU '{profile_in.sku}' already exists."
            )

    # Verify emission factor if provided
    if profile_in.emission_factor_id is not None:
        ef_res = await db.execute(select(EmissionFactor).filter(EmissionFactor.id == profile_in.emission_factor_id))
        if not ef_res.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Emission Factor with ID {profile_in.emission_factor_id} not found."
            )

    new_profile = ProductESGProfile(
        product_name=profile_in.product_name,
        sku=profile_in.sku,
        category=profile_in.category,
        emission_factor_id=profile_in.emission_factor_id,
        sustainability_score=profile_in.sustainability_score,
        lifecycle_notes=profile_in.lifecycle_notes,
        status=StatusEnum.ACTIVE
    )
    db.add(new_profile)
    await db.commit()
    await db.refresh(new_profile)
    return new_profile

@router.get("/", response_model=List[ProductESGProfileRead])
async def list_product_profiles(
    status: Optional[StatusEnum] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    query = select(ProductESGProfile)
    if status:
        query = query.filter(ProductESGProfile.status == status)

    query = query.offset(offset).limit(limit).order_by(ProductESGProfile.id)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{id}", response_model=ProductESGProfileRead)
async def get_product_profile(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    result = await db.execute(select(ProductESGProfile).filter(ProductESGProfile.id == id))
    profile = result.scalars().first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product ESG Profile with ID {id} not found."
        )
    return profile

@router.patch("/{id}", response_model=ProductESGProfileRead)
async def update_product_profile(
    id: int,
    profile_in: ProductESGProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(require_role("Admin"))
):
    result = await db.execute(select(ProductESGProfile).filter(ProductESGProfile.id == id))
    profile = result.scalars().first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product ESG Profile with ID {id} not found."
        )

    # Check duplicate SKU if provided and different
    if profile_in.sku is not None and profile_in.sku != profile.sku:
        sku_res = await db.execute(select(ProductESGProfile).filter(ProductESGProfile.sku == profile_in.sku))
        if sku_res.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product ESG Profile with SKU '{profile_in.sku}' already exists."
            )

    # Verify emission factor if provided
    if profile_in.emission_factor_id is not None:
        ef_res = await db.execute(select(EmissionFactor).filter(EmissionFactor.id == profile_in.emission_factor_id))
        if not ef_res.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Emission Factor with ID {profile_in.emission_factor_id} not found."
            )

    update_data = profile_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(profile, key, value)

    await db.commit()
    await db.refresh(profile)
    return profile

@router.delete("/{id}", response_model=ProductESGProfileRead)
async def delete_product_profile(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(require_role("Admin"))
):
    result = await db.execute(select(ProductESGProfile).filter(ProductESGProfile.id == id))
    profile = result.scalars().first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product ESG Profile with ID {id} not found."
        )

    # Soft delete
    profile.status = StatusEnum.INACTIVE
    await db.commit()
    await db.refresh(profile)
    return profile
