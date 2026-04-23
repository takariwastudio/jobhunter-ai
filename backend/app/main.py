from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.database import init_db
from app.config import get_settings
from app.routers import cv_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up...")
    await init_db()
    print("Database initialized")
    yield
    print("Shutting down...")


app = FastAPI(
    title="JobHunter AI API",
    description="API for AI-powered CV parsing and job matching",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cv_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "JobHunter AI API", "version": "0.1.0", "docs": "/docs"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
