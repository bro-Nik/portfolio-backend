"""Rate limiting для защиты API от злоупотреблений.

Использует IP адрес для идентификации клиента.
Требует request: Request в роутах
"""

from fastapi import Request
from limits.storage import RedisStorage
from redis.exceptions import ConnectionError as RedisConnectionError, RedisError
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.redis import redis_client


def get_real_ip(request: Request) -> str:
    """Получить IP клиента с учетом прокси."""
    # Заголовки в порядке приоритета
    ip_headers = ['X-Real-IP', 'CF-Connecting-IP', 'True-Client-IP', 'X-Forwarded-For']

    for header in ip_headers:
        if ip := request.headers.get(header):
            return ip.split(',')[0].strip()

    return get_remote_address(request) or 'unknown'


limiter = Limiter(key_func=get_real_ip)


async def connect_redis_to_limiter() -> None:
    """Подключаем Redis к существующему limiter."""
    try:
        async with redis_client.get_redis_session() as redis:
            limiter.storage = RedisStorage(redis)
    except (RedisError, RedisConnectionError, TimeoutError):
        # Продолжаем работу с memory storage
        pass
