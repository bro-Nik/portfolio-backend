"""Общие ответы API для обработки ошибок.

Использование:
    # Базовые коды для всех эндпоинтов роутера
    router = APIRouter(responses=responses(401, 429, 500))

    # Для конкретного эндпоинта добавляем только специфичные коды
    @router.post('/', status_code=201, responses=responses(400, 403, 409))
    async def create_item(data: CreateSchema): ...

ВАЖНО:
    - 200/201 - берутся из response_model/status_code
    - 422 - добавляется FastAPI автоматически
"""

from app.schemas import ErrorResponse

RESPONSES = {
    400: {'model': ErrorResponse},
    401: {'model': ErrorResponse},
    403: {'model': ErrorResponse},
    404: {'model': ErrorResponse},
    409: {'model': ErrorResponse},
    429: {'model': ErrorResponse},
    500: {'model': ErrorResponse},
}


def responses(*codes: int) -> dict:
    """Формирует responses на основе кодов ответов.

    - 200/201/422 автоматически исключаются
    - 200/201 - из response_model и status_code
    - 422 - FastAPI добавляет автоматически
    """
    skip = {200, 201, 422}
    return {code: RESPONSES[code] for code in codes if code not in skip}
