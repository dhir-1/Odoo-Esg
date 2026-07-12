from fastapi import APIRouter
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.departments import router as departments_router
from app.api.v1.endpoints.carbon import router as carbon_router
from app.api.v1.endpoints.social import router as social_router
from app.api.v1.endpoints.gamification import router as gamification_router
from app.api.v1.endpoints.governance import router as governance_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(departments_router, prefix="/departments", tags=["departments"])
api_router.include_router(carbon_router, prefix="/carbon-transactions", tags=["carbon-transactions"])
api_router.include_router(social_router, prefix="/csr", tags=["social-initiatives"])
api_router.include_router(gamification_router, prefix="/challenges", tags=["gamification"])
api_router.include_router(governance_router, prefix="/governance", tags=["governance"])
