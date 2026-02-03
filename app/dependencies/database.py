from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from app.core.database import AsyncSessionLocal

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


@asynccontextmanager
async def get_async_db_session() -> AsyncIterator['AsyncSession']:
    """Асинхронный контекстный менеджер для сессии БД."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_db_session() -> AsyncIterator['AsyncSession']:
    """FastAPI dependency для получения асинхронной сессии БД."""
    async with get_async_db_session() as session:
        yield session
