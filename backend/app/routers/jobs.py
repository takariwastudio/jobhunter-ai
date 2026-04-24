import uuid
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.saved_job import SavedJob
from app.models.user import User
from app.routers.auth import get_current_user
from app.services.job_search_service import search_jobs

router = APIRouter(prefix="/jobs", tags=["Jobs"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class JobResultResponse(BaseModel):
    external_id: str
    title: str
    company: str
    description: str
    source: str
    source_url: str
    location: Optional[str] = None
    salary_range: Optional[str] = None
    job_type: Optional[str] = None
    remote: Optional[bool] = None
    posted_date: Optional[datetime] = None
    is_saved: bool = False


class SaveJobRequest(BaseModel):
    external_id: str
    source: str
    title: str
    company: str
    description: str
    location: Optional[str] = None
    salary_range: Optional[str] = None
    job_type: Optional[str] = None
    remote: Optional[bool] = None
    source_url: Optional[str] = None
    posted_date: Optional[datetime] = None


class SavedJobResponse(BaseModel):
    id: uuid.UUID
    external_id: str
    source: str
    title: str
    company: str
    description: str
    location: Optional[str] = None
    salary_range: Optional[str] = None
    job_type: Optional[str] = None
    remote: Optional[bool] = None
    source_url: Optional[str] = None
    posted_date: Optional[datetime] = None
    saved_at: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/search", response_model=List[JobResultResponse])
async def search(
    q: str = Query(..., min_length=1, description="Palabras clave"),
    location: str = Query("", description="Ciudad o región"),
    country: str = Query("es", description="Código de país: es, mx, ar, co, br, us, gb…"),
    remote: Optional[bool] = Query(None, description="Solo empleos remotos"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    source: str = Query("all", description="adzuna | jsearch | all"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        results = await search_jobs(
            query=q,
            location=location,
            country=country,
            remote=remote,
            page=page,
            results_per_page=limit,
            source=source,
        )
    except Exception as e:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Error al buscar empleos: {e}")

    saved_ids: set[str] = set()
    if results:
        external_ids = [r.external_id for r in results]
        rows = await db.execute(
            select(SavedJob.external_id).where(
                and_(
                    SavedJob.user_id == current_user.id,
                    SavedJob.external_id.in_(external_ids),
                )
            )
        )
        saved_ids = {row[0] for row in rows.fetchall()}

    return [
        JobResultResponse(
            external_id=r.external_id,
            title=r.title,
            company=r.company,
            description=r.description,
            source=r.source,
            source_url=r.source_url,
            location=r.location,
            salary_range=r.salary_range,
            job_type=r.job_type,
            remote=r.remote,
            posted_date=r.posted_date,
            is_saved=r.external_id in saved_ids,
        )
        for r in results
    ]


@router.post("/save", response_model=SavedJobResponse, status_code=status.HTTP_201_CREATED)
async def save_job(
    body: SaveJobRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = await db.execute(
        select(SavedJob).where(
            and_(
                SavedJob.user_id == current_user.id,
                SavedJob.external_id == body.external_id,
                SavedJob.source == body.source,
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status.HTTP_409_CONFLICT, "Este empleo ya está guardado")

    job = SavedJob(user_id=current_user.id, **body.model_dump())
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


@router.delete("/save/{external_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unsave_job(
    external_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(SavedJob).where(
            and_(
                SavedJob.user_id == current_user.id,
                SavedJob.external_id == external_id,
            )
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Empleo no encontrado en guardados")
    await db.delete(job)
    await db.commit()


@router.get("/saved", response_model=List[SavedJobResponse])
async def get_saved_jobs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 50,
):
    result = await db.execute(
        select(SavedJob)
        .where(SavedJob.user_id == current_user.id)
        .order_by(SavedJob.saved_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()
