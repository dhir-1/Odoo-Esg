from fastapi import APIRouter
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.departments import router as departments_router
from app.api.v1.endpoints.carbon import router as carbon_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(departments_router, prefix="/departments", tags=["departments"])
api_router.include_router(carbon_router, prefix="/carbon-transactions", tags=["carbon-transactions"])
