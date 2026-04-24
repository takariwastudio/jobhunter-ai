import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.cv import CV, ParsedProfile
from app.models.user import User
from app.schemas.cv import ParsedProfileData, ExperienceItem, EducationItem, SkillItem, LanguageItem
from app.schemas.match import MatchRequest, MatchResponse, MatchScore
from app.services.ai_service import AIService
from app.routers.auth import get_current_user

router = APIRouter(prefix="/match", tags=["Match"])


@router.post("/jobs", response_model=MatchResponse)
async def match_jobs(
    request: MatchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Score the compatibility between the user's CV profile and a list of jobs."""
    cv_result = await db.execute(
        select(CV).where(CV.id == request.cv_id, CV.user_id == current_user.id)
    )
    if not cv_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CV no encontrado")

    profile_result = await db.execute(
        select(ParsedProfile).where(ParsedProfile.cv_id == request.cv_id)
    )
    profile_db = profile_result.scalar_one_or_none()
    if not profile_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil no encontrado. Procesa el CV primero.",
        )

    profile = ParsedProfileData(
        full_name=profile_db.full_name,
        email=profile_db.email,
        phone=profile_db.phone,
        summary=profile_db.summary,
        experience=[ExperienceItem(**exp) for exp in (profile_db.experience or [])],
        education=[EducationItem(**edu) for edu in (profile_db.education or [])],
        skills=[SkillItem(**skill) for skill in (profile_db.skills or [])],
        languages=[LanguageItem(**lang) for lang in (profile_db.languages or [])],
    )

    if not request.jobs:
        return MatchResponse(results=[], profile_name=profile.full_name)

    jobs_data = [
        {
            "external_id": job.external_id,
            "title": job.title,
            "company": job.company,
            "description": job.description,
        }
        for job in request.jobs
    ]

    try:
        ai = AIService()
        raw_results = await ai.batch_match_scores(profile, jobs_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al calcular compatibilidad: {str(e)}",
        )

    results = []
    for r in raw_results:
        try:
            results.append(
                MatchScore(
                    external_id=r.get("external_id", ""),
                    score=max(0, min(100, int(r.get("score", 0)))),
                    reasoning=r.get("reasoning", ""),
                    matching_skills=r.get("matching_skills", []),
                    missing_skills=r.get("missing_skills", []),
                    recommendation=r.get("recommendation", "partial_match"),
                )
            )
        except Exception:
            continue

    results.sort(key=lambda x: x.score, reverse=True)
    return MatchResponse(results=results, profile_name=profile.full_name)
