import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    # id matches Supabase auth.users.id — set explicitly on creation, never auto-generated
    id = Column(UUID(as_uuid=True), primary_key=True)
    email = Column(String, unique=True, index=True, nullable=True)
    phone = Column(String, unique=True, index=True, nullable=True)
    display_name = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    provider = Column(String, default="email")  # email | phone | google | github | apple
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    cvs = relationship("CV", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.email or self.phone}>"
