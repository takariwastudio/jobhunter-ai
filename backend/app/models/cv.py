import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum
from app.database import Base


class CVStatus(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"


class CV(Base):
    __tablename__ = "cvs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    mime_type = Column(String, nullable=True)
    status = Column(String, default=CVStatus.PENDING.value)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="cvs")
    parsed_profile = relationship("ParsedProfile", back_populates="cv", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<CV {self.original_filename}>"


class ParsedProfile(Base):
    __tablename__ = "parsed_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cv_id = Column(UUID(as_uuid=True), ForeignKey("cvs.id"), unique=True, nullable=False)

    # Contact info
    full_name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    summary = Column(Text, nullable=True)

    # Structured data as JSONB
    experience = Column(JSONB, default=list)
    education = Column(JSONB, default=list)
    skills = Column(JSONB, default=list)
    languages = Column(JSONB, default=list)
    raw_text = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    cv = relationship("CV", back_populates="parsed_profile")

    def __repr__(self):
        return f"<ParsedProfile {self.full_name}>"
