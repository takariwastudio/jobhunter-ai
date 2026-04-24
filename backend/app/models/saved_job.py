import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base


class SavedJob(Base):
    __tablename__ = "saved_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    external_id = Column(String, nullable=False)
    source = Column(String, nullable=False)  # adzuna | jsearch
    title = Column(String, nullable=False)
    company = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    location = Column(String, nullable=True)
    salary_range = Column(String, nullable=True)
    job_type = Column(String, nullable=True)
    remote = Column(Boolean, nullable=True)
    source_url = Column(String, nullable=True)
    posted_date = Column(DateTime, nullable=True)
    raw_data = Column(JSONB, default=dict)

    saved_at = Column(DateTime, default=datetime.utcnow)
