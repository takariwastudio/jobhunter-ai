from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "JobHunter AI"
    DEBUG: bool = False
    SECRET_KEY: str = "super-secret-key-change-in-production"

    # Database
    DATABASE_URL: str = "postgresql://jobhunter:jobhunter123@localhost:5432/jobhunter"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Anthropic
    ANTHROPIC_API_KEY: str = ""

    # Supabase Storage
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_KEY: str = ""
    SUPABASE_BUCKET: str = "cvs"

    # File Upload
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB

    # CORS — comma-separated: "https://a.com,https://b.com"
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
