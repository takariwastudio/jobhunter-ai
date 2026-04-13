from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum
import uuid


class CVStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"


class ExperienceItem(BaseModel):
    company: str
    title: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None


class EducationItem(BaseModel):
    institution: str
    degree: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class SkillItem(BaseModel):
    name: str
    category: str = Field(..., description="technical or soft")
    level: Optional[str] = Field(None, description="beginner, intermediate, advanced, expert")


class LanguageItem(BaseModel):
    name: str
    level: str = Field(..., description="basic, conversational, fluent, native")


class ParsedProfileData(BaseModel):
    """Structured data extracted from CV by AI."""
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    summary: Optional[str] = None
    experience: List[ExperienceItem] = Field(default_factory=list)
    education: List[EducationItem] = Field(default_factory=list)
    skills: List[SkillItem] = Field(default_factory=list)
    languages: List[LanguageItem] = Field(default_factory=list)
    raw_text: Optional[str] = None


class CVBase(BaseModel):
    original_filename: str


class CVCreate(CVBase):
    pass


class CVUpdate(BaseModel):
    parsed_data: Optional[ParsedProfileData] = None


class CVResponse(CVBase):
    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    file_path: str
    parsed_data: Optional[ParsedProfileData] = None
    status: CVStatus
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
