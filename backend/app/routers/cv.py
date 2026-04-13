import os
import uuid
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.database import get_db
from app.models.cv import CV, ParsedProfile, CVStatus
from app.schemas.cv import CVResponse, CVUpdate, ParsedProfileData
from app.services.cv_parser import CVParser
from app.services.ai_service import AIService
from app.config import get_settings

router = APIRouter(prefix="/cvs", tags=["CVs"])

settings = get_settings()

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)


@router.post("/upload", response_model=CVResponse, status_code=status.HTTP_201_CREATED)
async def upload_cv(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a CV file and process it with AI.

    Supports: PDF, DOCX, TXT, PNG, JPG
    """
    # Validate file size
    contents = await file.read()
    if len(contents) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is {settings.MAX_FILE_SIZE / 1024 / 1024}MB"
        )

    # Generate unique filename
    file_id = str(uuid.uuid4())
    original_filename = file.filename or "unnamed"
    file_extension = os.path.splitext(original_filename)[1]
    new_filename = f"{file_id}{file_extension}"
    file_path = os.path.join(settings.UPLOAD_DIR, new_filename)

    # Save file
    try:
        with open(file_path, "wb") as f:
            f.write(contents)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )

    # Detect MIME type
    parser = CVParser()
    mime_type = parser.detect_file_type(file_path)

    # Validate file type
    if not parser.is_supported(mime_type):
        os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {mime_type}. Supported types: PDF, DOCX, TXT, PNG, JPG"
        )

    # Create CV record
    cv = CV(
        original_filename=original_filename,
        file_path=file_path,
        mime_type=mime_type,
        status=CVStatus.PENDING.value
    )
    db.add(cv)
    await db.commit()
    await db.refresh(cv)

    return cv


@router.post("/{cv_id}/parse", response_model=ParsedProfileData)
async def parse_cv(
    cv_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Parse an uploaded CV using AI to extract structured information.
    """
    # Get CV
    result = await db.execute(
        select(CV).where(CV.id == cv_id)
    )
    cv = result.scalar_one_or_none()

    if not cv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CV not found"
        )

    # Update status to processing
    cv.status = CVStatus.PROCESSING.value
    await db.commit()

    try:
        # Extract text from file
        parser = CVParser()
        cv_text = parser.extract_text(cv.file_path, cv.mime_type)

        # Parse with AI
        ai_service = AIService()
        parsed_data = await ai_service.parse_cv(cv_text)

        # Save or update parsed profile
        result = await db.execute(
            select(ParsedProfile).where(ParsedProfile.cv_id == cv_id)
        )
        existing_profile = result.scalar_one_or_none()

        if existing_profile:
            # Update existing
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
            # Create new
            profile = ParsedProfile(
                cv_id=cv_id,
                full_name=parsed_data.full_name,
                email=parsed_data.email,
                phone=parsed_data.phone,
                summary=parsed_data.summary,
                experience=[exp.model_dump() for exp in parsed_data.experience],
                education=[edu.model_dump() for edu in parsed_data.education],
                skills=[skill.model_dump() for skill in parsed_data.skills],
                languages=[lang.model_dump() for lang in parsed_data.languages],
                raw_text=parsed_data.raw_text
            )
            db.add(profile)

        # Update CV status
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
            detail=f"Failed to parse CV: {str(e)}"
        )


@router.get("/{cv_id}/profile", response_model=ParsedProfileData)
async def get_profile(
    cv_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get the parsed profile for a CV.
    """
    result = await db.execute(
        select(ParsedProfile).where(ParsedProfile.cv_id == cv_id)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found. Have you parsed this CV?"
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
        raw_text=profile.raw_text
    )


@router.put("/{cv_id}/profile", response_model=ParsedProfileData)
async def update_profile(
    cv_id: uuid.UUID,
    profile_data: ParsedProfileData,
    db: AsyncSession = Depends(get_db)
):
    """
    Update the parsed profile manually.
    """
    result = await db.execute(
        select(ParsedProfile).where(ParsedProfile.cv_id == cv_id)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )

    # Update fields
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
    db: AsyncSession = Depends(db),
    skip: int = 0,
    limit: int = 100
):
    """
    List all uploaded CVs.
    """
    result = await db.execute(
        select(CV).offset(skip).limit(limit).order_by(CV.created_at.desc())
    )
    cvs = result.scalars().all()
    return cvs


@router.get("/{cv_id}", response_model=CVResponse)
async def get_cv(
    cv_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific CV by ID.
    """
    result = await db.execute(
        select(CV).where(CV.id == cv_id)
    )
    cv = result.scalar_one_or_none()

    if not cv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CV not found"
        )

    return cv


@router.delete("/{cv_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cv(
    cv_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a CV and its associated file.
    """
    result = await db.execute(
        select(CV).where(CV.id == cv_id)
    )
    cv = result.scalar_one_or_none()

    if not cv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CV not found"
        )

    # Delete file if it exists
    if os.path.exists(cv.file_path):
        try:
            os.remove(cv.file_path)
        except Exception:
            pass  # Ignore file deletion errors

    await db.delete(cv)
    await db.commit()

    return None
