from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "JobHunter AI"
    DEBUG: bool = False
    SECRET_KEY: str = "super-secret-key-change-in-production"

    # Database
    DATABASE_URL: str = ""

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Anthropic
    ANTHROPIC_API_KEY: str = ""

    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""       # Public key — used for auth API calls
    SUPABASE_SERVICE_KEY: str = ""    # Admin key — used for storage
    SUPABASE_JWT_SECRET: str = ""     # From Dashboard > Settings > API > JWT Settings
    SUPABASE_BUCKET: str = "cvs"

    # Auth / URLs
    FRONTEND_URL: str = "http://localhost:5173"
    BACKEND_URL: str = "http://localhost:8000"

    # Cookie settings
    COOKIE_SECURE: bool = False  # True in production (HTTPS only)
    COOKIE_SAMESITE: str = "lax"

    # Job Search APIs
    ADZUNA_APP_ID: str = ""
    ADZUNA_APP_KEY: str = ""
    JSEARCH_API_KEY: str = ""

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
