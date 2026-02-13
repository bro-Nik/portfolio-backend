from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool

from app.core.config import settings


class RedisClient:
    """Асинхронный клиент Redis с пулом соединений."""

    def __init__(self) -> None:
        self._pool: ConnectionPool | None = None

    async def initialize(self) -> None:
        """Инициализация пула соединений Redis."""
        if self._pool is None:
            self._pool = ConnectionPool.from_url(
                str(settings.redis_url),
                max_connections=settings.redis_max_connections,
                socket_timeout=settings.redis_timeout,
                socket_connect_timeout=settings.redis_timeout,
                decode_responses=True,
            )

    async def close(self) -> None:
        """Закрыть пул соединений Redis."""
        if self._pool is not None:
            await self._pool.disconnect()
            self._pool = None

    @asynccontextmanager
    async def get_redis_session(self) -> AsyncIterator[redis.Redis]:
        """Асинхронный контекстный менеджер для Redis соединения."""
        if self._pool is None:
            await self.initialize()
        
        client = redis.Redis(connection_pool=self._pool)
        try:
            yield client
        finally:
            await client.close()


redis_client = RedisClient()
