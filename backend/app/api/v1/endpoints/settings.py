from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.employee import Employee
from app.core.permissions import require_role
from app.services.settings import get_esg_config
from app.schemas.settings import (
    ESGConfigurationRead,
    ESGConfigurationUpdate,
    NotificationPreferencesRead,
    NotificationPreferencesUpdate
)

router = APIRouter()


@router.get("/esg-configuration", response_model=ESGConfigurationRead, summary="Get ESG Weights and Flags")
async def read_esg_configuration(
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(require_role("Admin"))
):
    """
    Retrieves the current singleton ESGConfiguration containing sub-score weights and toggles.
    Only accessible to Administrators.
    """
    return await get_esg_config(db)


@router.patch("/esg-configuration", response_model=ESGConfigurationRead, summary="Update ESG Weights and Flags")
async def update_esg_configuration(
    config_in: ESGConfigurationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(require_role("Admin"))
):
    """
    Updates sub-score weights and general toggles on the singleton ESGConfiguration row.
    Validates that environmental + social + governance weights sum to exactly 1.0.
    Returns HTTP 422 if the sum validation fails.
    Only accessible to Administrators.
    """
    config = await get_esg_config(db)

    # Convert incoming updates
    update_data = config_in.model_dump(exclude_unset=True)

    # Determine prospective weights
    env_w = update_data.get("environmental_weight", config.environmental_weight)
    soc_w = update_data.get("social_weight", config.social_weight)
    gov_w = update_data.get("governance_weight", config.governance_weight)

    # Validate weight sum matches 1.0 (with safe precision rounding)
    total_w = float(env_w) + float(soc_w) + float(gov_w)
    if round(total_w, 4) != 1.0000:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"The sum of ESG weights must equal exactly 1.0. Got: {total_w}"
        )

    # Apply valid updates
    for key, val in update_data.items():
        setattr(config, key, val)

    await db.commit()
    await db.refresh(config)
    return config


@router.get("/notification-preferences", response_model=NotificationPreferencesRead, summary="Get Notification Toggles")
async def read_notification_preferences(
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(require_role("Admin"))
):
    """
    Exposes exactly the four toggles displayed on the frontend settings screen.
    Only accessible to Administrators.
    """
    return await get_esg_config(db)


@router.patch("/notification-preferences", response_model=NotificationPreferencesRead, summary="Update Notification Toggles")
async def update_notification_preferences(
    prefs_in: NotificationPreferencesUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(require_role("Admin"))
):
    """
    Updates the four settings screen toggles on the singleton ESGConfiguration row.
    Only accessible to Administrators.
    """
    config = await get_esg_config(db)

    # Apply updates
    update_data = prefs_in.model_dump(exclude_unset=True)
    for key, val in update_data.items():
        setattr(config, key, val)

    await db.commit()
    await db.refresh(config)
    return config
