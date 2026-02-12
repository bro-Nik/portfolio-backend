"""Транзакции в активах портфелей и кошельков пользователя.

Все эндпоинты требуют валидный access token
"""

# TODO: Добавить responses для автодокументации


from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.core.exceptions import service_exception_handler
from app.core.rate_limit import limiter
from app.dependencies import User, get_current_user, get_transaction_service
from app.schemas import TransactionCreateRequest, TransactionResponseWithAssets
from app.services import TransactionService

router = APIRouter(prefix='/transactions', tags=['Transactions'])


@router.post('/')
@limiter.limit('5/minute')
@service_exception_handler('Ошибка при создании транзакции')
async def create_transaction(
    request: Request,
    transaction_data: TransactionCreateRequest,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[TransactionService, Depends(get_transaction_service)],
) -> TransactionResponseWithAssets:
    """Создание новой транзакции."""
    return await service.create_transaction(user.id, transaction_data)


@router.put('/{transaction_id}')
@limiter.limit('5/minute')
@service_exception_handler('Ошибка при изменении транзакции')
async def update_transaction(
    request: Request,
    transaction_id: int,
    transaction_data: TransactionCreateRequest,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[TransactionService, Depends(get_transaction_service)],
) -> TransactionResponseWithAssets:
    """Изменение транзакции."""
    return await service.update_transaction(user.id, transaction_id, transaction_data)


@router.delete('/{transaction_id}')
@limiter.limit('5/minute')
@service_exception_handler('Ошибка при удалении транзакции')
async def delete_transaction(
    request: Request,
    transaction_id: int,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[TransactionService, Depends(get_transaction_service)],
) -> TransactionResponseWithAssets:
    """Удаление транзакции."""
    return await service.delete_transaction(user.id, transaction_id)
