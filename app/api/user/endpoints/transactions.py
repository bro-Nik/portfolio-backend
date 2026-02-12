"""Транзакции в активах портфелей и кошельков пользователя.

Все эндпоинты требуют валидный access token
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.core.exceptions import service_exception_handler
from app.core.rate_limit import limiter
from app.core.responses import responses
from app.dependencies import User, get_current_user, get_transaction_service
from app.schemas import TransactionCreateRequest, TransactionResponseWithAssets
from app.services import TransactionService

router = APIRouter(prefix='/transactions', tags=['Transactions'], responses=responses(401, 429, 500))


@router.post('/', status_code=201, responses=responses(400, 404, 409))
@limiter.limit('5/minute')
@service_exception_handler('Ошибка при создании транзакции')
async def create_transaction(
    request: Request,
    data: TransactionCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    transaction_service: Annotated[TransactionService, Depends(get_transaction_service)],
) -> TransactionResponseWithAssets:
    """Создание новой транзакции."""
    return await transaction_service.create(current_user.id, data)


@router.put('/{transaction_id}', responses=responses(400, 404, 409))
@limiter.limit('5/minute')
@service_exception_handler('Ошибка при изменении транзакции')
async def update_transaction(
    request: Request,
    transaction_id: int,
    data: TransactionCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    transaction_service: Annotated[TransactionService, Depends(get_transaction_service)],
) -> TransactionResponseWithAssets:
    """Изменение транзакции."""
    return await transaction_service.update(current_user.id, transaction_id, data)


@router.delete('/{transaction_id}', responses=responses(400, 404))
@limiter.limit('5/minute')
@service_exception_handler('Ошибка при удалении транзакции')
async def delete_transaction(
    request: Request,
    transaction_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    transaction_service: Annotated[TransactionService, Depends(get_transaction_service)],
) -> TransactionResponseWithAssets:
    """Удаление транзакции."""
    return await transaction_service.delete(current_user.id, transaction_id)
