from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.core.config import settings

from sqlalchemy.engine.url import make_url

# Parse and clean DATABASE_URL for asyncpg compatibility
raw_url = settings.DATABASE_URL
url_obj = make_url(raw_url)

# Convert driver to postgresql+asyncpg and clear query string params (like sslmode) that break asyncpg
clean_url = url_obj.set(drivername="postgresql+asyncpg", query={}).render_as_string(hide_password=False)

connect_args = {}
if "neon.tech" in raw_url or "sslmode=" in raw_url or "ssl=" in raw_url:
    connect_args["ssl"] = "require"

engine = create_async_engine(
    clean_url,
    echo=False,
    connect_args=connect_args,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
