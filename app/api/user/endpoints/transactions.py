"""Транзакции в активах портфелей и кошельков пользователя.

Все эндпоинты требуют валидный access token
"""

# TODO: Добавить responses для автодокументации


from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.exceptions import service_exception_handler
from app.dependencies import User, get_current_user, get_transaction_service
from app.schemas import TransactionCreateRequest, TransactionResponseWithAssets
from app.services.transaction import TransactionService

router = APIRouter(prefix='/transactions', tags=['Transactions'])


@router.post('/')
@service_exception_handler('Ошибка при создании транзакции')
async def create_transaction(
    transaction_data: TransactionCreateRequest,
    user: Annotated[User, Depends(get_current_user)],
    transaction_service: Annotated[TransactionService, Depends(get_transaction_service)],
) -> TransactionResponseWithAssets:
    """Создание новой транзакции."""
    transaction = await transaction_service.create_transaction(user.id, transaction_data)

    return TransactionResponseWithAssets(
        message='Транзакция успешно создана',
        # Измененные активы на основе созданной транзакции
        portfolio_assets=await transaction_service.get_affected_portfolio_assets((transaction,)),
        wallet_assets=await transaction_service.get_affected_wallet_assets((transaction,)),
    )


@router.put('/{transaction_id}')
@service_exception_handler('Ошибка при изменении транзакции')
async def update_transaction(
    transaction_id: int,
    transaction_data: TransactionCreateRequest,
    user: Annotated[User, Depends(get_current_user)],
    transaction_service: Annotated[TransactionService, Depends(get_transaction_service)],
) -> TransactionResponseWithAssets:
    """Изменение транзакции."""
    # Новая и старая транзакция
    transactions = await transaction_service.update_transaction(user.id, transaction_id, transaction_data)

    return TransactionResponseWithAssets(
        message='Транзакция успешно изменена',
        # Измененные активы на основе измененной транзакции
        portfolio_assets=await transaction_service.get_affected_portfolio_assets(transactions),
        wallet_assets=await transaction_service.get_affected_wallet_assets(transactions),
    )


@router.delete('/{transaction_id}')
@service_exception_handler('Ошибка при удалении транзакции')
async def delete_transaction(
    transaction_id: int,
    user: Annotated[User, Depends(get_current_user)],
    transaction_service: Annotated[TransactionService, Depends(get_transaction_service)],
) -> TransactionResponseWithAssets:
    """Удаление транзакции."""
    transaction = await transaction_service.delete_transaction(user.id, transaction_id)

    return TransactionResponseWithAssets(
        message='Транзакция успешно удалена',
        # Измененные активы на основе удаленной транзакции
        portfolio_assets=await transaction_service.get_affected_portfolio_assets((transaction,)),
        wallet_assets=await transaction_service.get_affected_wallet_assets((transaction,)),
    )
