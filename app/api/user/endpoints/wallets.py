"""Кошельки пользователя и их активы.

Все эндпоинты требуют валидный access token
"""

# TODO: Добавить responses для автодокументации


from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.core.exceptions import service_exception_handler
from app.core.rate_limit import limiter
from app.dependencies import User, get_current_user, get_wallet_asset_service, get_wallet_service
from app.dependencies.services import get_transaction_service
from app.schemas import (
    WalletAssetDetailResponse,
    WalletCreateRequest,
    WalletDeleteResponse,
    WalletListResponse,
    WalletResponse,
    WalletUpdateRequest,
)
from app.services import TransactionService, WalletAssetService, WalletService

router = APIRouter(prefix='/wallets', tags=['Wallets'])


@router.get('/')
@limiter.limit('5/minute')
@service_exception_handler('Ошибка при получении кошельков')
async def get_user_wallets(
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    wallet_service: Annotated[WalletService, Depends(get_wallet_service)],
) -> WalletListResponse:
    """Получение всех кошельков пользователя."""
    return await wallet_service.get_many(current_user.id)


@router.get('/{wallet_id}')
@limiter.limit('5/minute')
@service_exception_handler('Ошибка при получении кошелька')
async def get_user_wallet(
    request: Request,
    wallet_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    wallet_service: Annotated[WalletService, Depends(get_wallet_service)],
) -> WalletResponse:
    """Получение кошелька пользователя."""
    return await wallet_service.get(wallet_id, current_user.id)


@router.post('/', status_code=201)
@limiter.limit('5/minute')
@service_exception_handler('Ошибка при создании кошелька')
async def create_wallet(
    request: Request,
    data: WalletCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    wallet_service: Annotated[WalletService, Depends(get_wallet_service)],
) -> WalletResponse:
    """Создание нового кошелька."""
    return await wallet_service.create(current_user.id, data)


@router.put('/{wallet_id}')
@limiter.limit('5/minute')
@service_exception_handler('Ошибка при изменении кошелька')
async def update_wallet(
    request: Request,
    wallet_id: int,
    data: WalletUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    wallet_service: Annotated[WalletService, Depends(get_wallet_service)],
) -> WalletResponse:
    """Обновление кошелька."""
    return await wallet_service.update(wallet_id, current_user.id, data)


@router.delete('/{wallet_id}')
@limiter.limit('5/minute')
@service_exception_handler('Ошибка при удалении кошелька')
async def delete_wallet(
    request: Request,
    wallet_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    wallet_service: Annotated[WalletService, Depends(get_wallet_service)],
) -> WalletDeleteResponse:
    """Удаление кошелька."""
    return await wallet_service.delete(wallet_id, current_user.id)


@router.get('/assets/{asset_id}')
@limiter.limit('5/minute')
@service_exception_handler('Ошибка при получении информации об активе')
async def get_asset(
    request: Request,
    asset_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    asset_service: Annotated[WalletAssetService, Depends(get_wallet_asset_service)],
    transaction_service: Annotated[TransactionService, Depends(get_transaction_service)],
) -> WalletAssetDetailResponse:
    """Получение детальной информации об активе."""
    asset, distribution = await asset_service.get_distribution(asset_id, current_user.id)
    transactions = await transaction_service.get_asset_transactions(asset)

    return WalletAssetDetailResponse(
        transactions=transactions,
        distribution=distribution,
    )
