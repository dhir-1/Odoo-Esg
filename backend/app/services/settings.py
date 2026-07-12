from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.settings import ESGConfiguration

async def get_esg_config(db: AsyncSession) -> ESGConfiguration:
    """
    Retrieves the singleton ESGConfiguration row (id=1).
    Creates it with default weights and flags if it does not exist.
    """
    result = await db.execute(select(ESGConfiguration).filter(ESGConfiguration.id == 1))
    config = result.scalars().first()
    if not config:
        config = ESGConfiguration(
            id=1,
            environmental_weight=0.40,
            social_weight=0.30,
            governance_weight=0.30,
            auto_emission_calculation_enabled=False,
            evidence_requirement_enabled=False,
            badge_auto_award_enabled=False
        )
        db.add(config)
        await db.commit()
        await db.refresh(config)
    return config
