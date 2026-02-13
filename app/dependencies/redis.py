from collections.abc import AsyncIterator

from redis.asyncio import Redis

from app.core.redis import redis_client


async def get_redis() -> AsyncIterator[Redis]:
    """FastAPI dependency для получения Redis клиента."""
    async with redis_client.get_redis_session() as client:
        yield client
