"""API route modules."""

from fastapi import APIRouter

from app.api.routes import ai, auth, plans, progress, study_days

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(plans.router)
api_router.include_router(study_days.router)
api_router.include_router(progress.router)
api_router.include_router(ai.router)

__all__ = ["api_router"]
