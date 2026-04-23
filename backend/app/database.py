from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.config import get_settings

settings = get_settings()


def _build_asyncpg_url(url: str) -> tuple[str, dict]:
    """Strip psycopg2-only params and return asyncpg URL + connect_args."""
    parsed = urlparse(url)
    params = parse_qs(parsed.query, keep_blank_values=True)

    needs_ssl = "sslmode" in params or "ssl" in params
    # Remove params asyncpg doesn't accept
    for key in ("sslmode", "channel_binding", "ssl"):
        params.pop(key, None)

    clean = parsed._replace(
        scheme="postgresql+asyncpg",
        query=urlencode({k: v[0] for k, v in params.items()}),
    )
    connect_args = {"ssl": True} if needs_ssl else {}
    return urlunparse(clean), connect_args


DATABASE_URL_ASYNC, _connect_args = _build_asyncpg_url(settings.DATABASE_URL)

# Async engine for async operations
async_engine = create_async_engine(
    DATABASE_URL_ASYNC,
    echo=settings.DEBUG,
    future=True,
    connect_args=_connect_args,
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Base class for models
Base = declarative_base()


async def get_db() -> AsyncSession:
    """Dependency for getting async database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database tables."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
