from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from app.database import init_db
from app.config import get_settings
from app.routers import cv_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # Startup
    print("Starting up...")
    await init_db()
    print("Database initialized")

    # Create upload directory
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    yield

    # Shutdown
    print("Shutting down...")


app = FastAPI(
    title="JobHunter AI API",
    description="API for AI-powered CV parsing and job matching",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(cv_router, prefix="/api/v1")

# Static files for uploads
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")


@app.get("/")
async def root():
    return {
        "message": "JobHunter AI API",
        "version": "0.1.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
