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
    transaction = await service.create_transaction(user.id, transaction_data)

    return TransactionResponseWithAssets(
        message='Транзакция успешно создана',
        transaction=transaction,
        portfolio_assets=await service.get_affected_portfolio_assets((transaction,)),
        wallet_assets=await service.get_affected_wallet_assets((transaction,)),
    )


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
    # Новая и старая транзакция
    transactions = await service.update_transaction(user.id, transaction_id, transaction_data)
    updated_transaction = transactions[1]

    return TransactionResponseWithAssets(
        message='Транзакция успешно изменена',
        transaction=updated_transaction,
        portfolio_assets=await service.get_affected_portfolio_assets(transactions),
        wallet_assets=await service.get_affected_wallet_assets(transactions),
    )


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
    transaction = await service.delete_transaction(user.id, transaction_id)

    return TransactionResponseWithAssets(
        message='Транзакция успешно удалена',
        portfolio_assets=await service.get_affected_portfolio_assets((transaction,)),
        wallet_assets=await service.get_affected_wallet_assets((transaction,)),
    )
