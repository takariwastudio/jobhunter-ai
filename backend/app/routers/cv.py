import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.database import get_db
from app.models.cv import CV, ParsedProfile, CVStatus
from app.models.user import User
from app.schemas.cv import (
    CVResponse,
    ParsedProfileData,
    ExperienceItem,
    EducationItem,
    SkillItem,
    LanguageItem,
)
from app.services.cv_parser import CVParser
from app.services.ai_service import AIService
from app.services.storage_service import StorageService
from app.config import get_settings
from app.routers.auth import get_current_user

router = APIRouter(prefix="/cvs", tags=["CVs"])
settings = get_settings()


@router.post("/upload", response_model=CVResponse, status_code=status.HTTP_201_CREATED)
async def upload_cv(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    contents = await file.read()
    if len(contents) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Archivo demasiado grande. Máximo {settings.MAX_FILE_SIZE / 1024 / 1024:.0f}MB",
        )

    parser = CVParser()
    mime_type = parser.detect_from_bytes(contents)
    if not parser.is_supported(mime_type):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Tipo de archivo no soportado: {mime_type}. Soportados: PDF, DOCX, TXT, PNG, JPG",
        )

    original_filename = file.filename or "unnamed"
    ext = original_filename.rsplit(".", 1)[-1] if "." in original_filename else "bin"
    file_key = f"{current_user.id}/{uuid.uuid4()}.{ext}"

    storage = StorageService()
    try:
        await storage.upload(file_key, contents, mime_type)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al subir el archivo: {str(e)}",
        )

    cv = CV(
        user_id=current_user.id,
        original_filename=original_filename,
        file_path=file_key,
        mime_type=mime_type,
        status=CVStatus.PENDING.value,
    )
    db.add(cv)
    await db.commit()
    await db.refresh(cv)
    return cv


@router.post("/{cv_id}/parse", response_model=ParsedProfileData)
async def parse_cv(
    cv_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(CV).where(CV.id == cv_id, CV.user_id == current_user.id)
    )
    cv = result.scalar_one_or_none()
    if not cv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CV no encontrado")

    cv.status = CVStatus.PROCESSING.value
    await db.commit()

    try:
        storage = StorageService()
        file_bytes = await storage.download(cv.file_path)

        parser = CVParser()
        cv_text = parser.extract_text_from_bytes(file_bytes, cv.mime_type)

        ai_service = AIService()
        parsed_data = await ai_service.parse_cv(cv_text)

        result = await db.execute(select(ParsedProfile).where(ParsedProfile.cv_id == cv_id))
        existing_profile = result.scalar_one_or_none()

        if existing_profile:
            existing_profile.full_name = parsed_data.full_name
            existing_profile.email = parsed_data.email
            existing_profile.phone = parsed_data.phone
            existing_profile.summary = parsed_data.summary
            existing_profile.experience = [exp.model_dump() for exp in parsed_data.experience]
            existing_profile.education = [edu.model_dump() for edu in parsed_data.education]
            existing_profile.skills = [skill.model_dump() for skill in parsed_data.skills]
            existing_profile.languages = [lang.model_dump() for lang in parsed_data.languages]
            existing_profile.raw_text = parsed_data.raw_text
            existing_profile.updated_at = datetime.utcnow()
        else:
            db.add(ParsedProfile(
                cv_id=cv_id,
                full_name=parsed_data.full_name,
                email=parsed_data.email,
                phone=parsed_data.phone,
                summary=parsed_data.summary,
                experience=[exp.model_dump() for exp in parsed_data.experience],
                education=[edu.model_dump() for edu in parsed_data.education],
                skills=[skill.model_dump() for skill in parsed_data.skills],
                languages=[lang.model_dump() for lang in parsed_data.languages],
                raw_text=parsed_data.raw_text,
            ))

        cv.status = CVStatus.COMPLETED.value
        cv.error_message = None
        await db.commit()
        return parsed_data

    except Exception as e:
        cv.status = CVStatus.ERROR.value
        cv.error_message = str(e)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar el CV: {str(e)}",
        )


@router.get("/{cv_id}/profile", response_model=ParsedProfileData)
async def get_profile(
    cv_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Verify ownership
    cv_result = await db.execute(
        select(CV).where(CV.id == cv_id, CV.user_id == current_user.id)
    )
    if not cv_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CV no encontrado")

    result = await db.execute(select(ParsedProfile).where(ParsedProfile.cv_id == cv_id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil no encontrado. ¿Ya procesaste este CV?",
        )
    return ParsedProfileData(
        full_name=profile.full_name,
        email=profile.email,
        phone=profile.phone,
        summary=profile.summary,
        experience=[ExperienceItem(**exp) for exp in (profile.experience or [])],
        education=[EducationItem(**edu) for edu in (profile.education or [])],
        skills=[SkillItem(**skill) for skill in (profile.skills or [])],
        languages=[LanguageItem(**lang) for lang in (profile.languages or [])],
        raw_text=profile.raw_text,
    )


@router.put("/{cv_id}/profile", response_model=ParsedProfileData)
async def update_profile(
    cv_id: uuid.UUID,
    profile_data: ParsedProfileData,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cv_result = await db.execute(
        select(CV).where(CV.id == cv_id, CV.user_id == current_user.id)
    )
    if not cv_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CV no encontrado")

    result = await db.execute(select(ParsedProfile).where(ParsedProfile.cv_id == cv_id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil no encontrado")

    profile.full_name = profile_data.full_name
    profile.email = profile_data.email
    profile.phone = profile_data.phone
    profile.summary = profile_data.summary
    profile.experience = [exp.model_dump() for exp in profile_data.experience]
    profile.education = [edu.model_dump() for edu in profile_data.education]
    profile.skills = [skill.model_dump() for skill in profile_data.skills]
    profile.languages = [lang.model_dump() for lang in profile_data.languages]
    profile.updated_at = datetime.utcnow()
    await db.commit()
    return profile_data


@router.get("/", response_model=List[CVResponse])
async def list_cvs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
):
    result = await db.execute(
        select(CV)
        .where(CV.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
        .order_by(CV.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{cv_id}", response_model=CVResponse)
async def get_cv(
    cv_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(CV).where(CV.id == cv_id, CV.user_id == current_user.id)
    )
    cv = result.scalar_one_or_none()
    if not cv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CV no encontrado")
    return cv


@router.delete("/{cv_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cv(
    cv_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(CV).where(CV.id == cv_id, CV.user_id == current_user.id)
    )
    cv = result.scalar_one_or_none()
    if not cv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CV no encontrado")

    storage = StorageService()
    try:
        await storage.delete(cv.file_path)
    except Exception:
        pass

    await db.delete(cv)
    await db.commit()
