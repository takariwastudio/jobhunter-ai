from .cv import router as cv_router
from .auth import router as auth_router
from .jobs import router as jobs_router

__all__ = ["cv_router", "auth_router", "jobs_router"]
