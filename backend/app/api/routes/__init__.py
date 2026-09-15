"""API route modules."""

from fastapi import APIRouter

from app.api.routes import plans, progress, study_days

api_router = APIRouter()
api_router.include_router(plans.router)
api_router.include_router(study_days.router)
api_router.include_router(progress.router)

__all__ = ["api_router"]
