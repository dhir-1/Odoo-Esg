from fastapi import APIRouter
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.departments import router as departments_router
from app.api.v1.endpoints.carbon import router as carbon_router
from app.api.v1.endpoints.social import router as social_router
from app.api.v1.endpoints.gamification import router as gamification_router
from app.api.v1.endpoints.governance import router as governance_router
from app.api.v1.endpoints.participation import router as participation_router
from app.api.v1.endpoints.categories import router as categories_router
from app.api.v1.endpoints.emission_factors import router as emission_factors_router
from app.api.v1.endpoints.product_esg_profiles import router as product_esg_profiles_router
from app.api.v1.endpoints.environmental_goals import router as environmental_goals_router
from app.api.v1.endpoints.badges import router as badges_router
from app.api.v1.endpoints.rewards import router as rewards_router
from app.api.v1.endpoints.gamification_services import router as gamification_services_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(departments_router, prefix="/departments", tags=["departments"])
api_router.include_router(carbon_router, prefix="/carbon-transactions", tags=["carbon-transactions"])
api_router.include_router(social_router, prefix="/csr", tags=["social-initiatives"])
api_router.include_router(gamification_router, prefix="/challenges", tags=["gamification"])
api_router.include_router(governance_router, prefix="/governance", tags=["governance"])
api_router.include_router(participation_router, prefix="/participation", tags=["unified-participation"])
api_router.include_router(categories_router, prefix="/categories", tags=["categories"])
api_router.include_router(emission_factors_router, prefix="/emission-factors", tags=["emission-factors"])
api_router.include_router(product_esg_profiles_router, prefix="/product-esg-profiles", tags=["product-esg-profiles"])
api_router.include_router(environmental_goals_router, prefix="/environmental-goals", tags=["environmental-goals"])
api_router.include_router(badges_router, prefix="/badges", tags=["badges"])
api_router.include_router(rewards_router, prefix="/rewards", tags=["rewards"])
api_router.include_router(gamification_services_router, tags=["gamification-services"])
