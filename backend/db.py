import logging
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text

from config import settings
from models.claim import Base

logger = logging.getLogger(__name__)

async_engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)

sync_engine = create_engine(
    settings.database_sync_url,
    echo=False,
    pool_size=5,
)

async_session_factory = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created/verified")


async def get_session() -> AsyncSession:
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


def get_sync_session() -> Session:
    session = Session(sync_engine)
    try:
        yield session
    finally:
        session.close()
