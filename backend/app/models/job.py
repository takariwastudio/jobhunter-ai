import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Job details
    title = Column(String, nullable=False, index=True)
    company = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=False)
    location = Column(String, nullable=True, index=True)
    salary_range = Column(String, nullable=True)
    job_type = Column(String, nullable=True)  # full-time, part-time, contract
    remote = Column(Boolean, default=False)

    # Source tracking
    source = Column(String, nullable=False)  # linkedin, indeed, adzuna, etc.
    source_url = Column(String, nullable=True)
    external_id = Column(String, nullable=True, index=True)
    posted_date = Column(DateTime, nullable=True)

    # Raw data storage
    raw_data = Column(JSONB, default=dict)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Job {self.title} at {self.company}>"
