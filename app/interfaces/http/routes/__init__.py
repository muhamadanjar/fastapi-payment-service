from fastapi import APIRouter
from .health import router as health_router

api_router = APIRouter()

# Include all routers with prefixes
api_router.include_router(health_router, prefix="/health", tags=["Health"])