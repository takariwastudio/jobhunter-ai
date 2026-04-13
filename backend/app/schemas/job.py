from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, HttpUrl
import uuid


class JobBase(BaseModel):
    title: str
    company: str
    description: str
    location: Optional[str] = None
    salary_range: Optional[str] = None
    job_type: Optional[str] = None  # full-time, part-time, contract, etc.
    remote: Optional[bool] = None
    source: str  # linkedin, indeed, etc.
    source_url: Optional[HttpUrl] = None
    external_id: Optional[str] = None


class JobCreate(JobBase):
    raw_data: Optional[Dict[str, Any]] = None


class JobUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    salary_range: Optional[str] = None
    job_type: Optional[str] = None


class JobResponse(JobBase):
    id: uuid.UUID
    posted_date: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
