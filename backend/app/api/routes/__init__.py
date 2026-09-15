"""API route modules."""

from fastapi import APIRouter

from app.api.routes import auth, plans, progress, study_days

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(plans.router)
api_router.include_router(study_days.router)
api_router.include_router(progress.router)

__all__ = ["api_router"]
