"""Rate limiting для защиты API от злоупотреблений.

Использует IP адрес для идентификации клиента.
Требует request: Request в роутах
"""

# TODO: Redis

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address


def get_real_ip(request: Request) -> str | None:
    """Получить IP клиента с учетом прокси."""
    # Заголовки в порядке приоритета
    ip_headers = ['X-Real-IP', 'CF-Connecting-IP', 'True-Client-IP', 'X-Forwarded-For']

    for header in ip_headers:
        ip = request.headers.get(header)
        if ip:
            # X-Forwarded-For может содержать цепочку: "client, proxy1, proxy2"
            # Берем первый IP (оригинальный клиент)
            return ip.split(',')[0].strip()

    return get_remote_address(request)


limiter = Limiter(key_func=get_real_ip)



