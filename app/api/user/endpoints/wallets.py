"""Кошельки пользователя и их активы.

Все эндпоинты требуют валидный access token
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.core.config import settings
from app.core.exceptions import service_exception_handler
from app.core.rate_limit import limiter
from app.core.responses import responses
from app.dependencies import User, get_current_user, get_wallet_asset_service, get_wallet_service
from app.schemas import (
    TransactionResponse,
    WalletCreateRequest,
    WalletDeleteResponse,
    WalletListResponse,
    WalletResponse,
    WalletUpdateRequest,
)
from app.services import WalletAssetService, WalletService

router = APIRouter(prefix='/wallets', tags=['Wallets'], responses=responses(401, 429, 500))


@router.get('/')
@limiter.limit(settings.rate_limit_auth)
@service_exception_handler('Ошибка при получении кошельков')
async def get_user_wallets(
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    wallet_service: Annotated[WalletService, Depends(get_wallet_service)],
) -> WalletListResponse:
    """Получение всех кошельков пользователя."""
    return await wallet_service.get_many(current_user.id)


@router.get('/{wallet_id}', responses=responses(404))
@limiter.limit(settings.rate_limit_auth)
@service_exception_handler('Ошибка при получении кошелька')
async def get_user_wallet(
    request: Request,
    wallet_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    wallet_service: Annotated[WalletService, Depends(get_wallet_service)],
) -> WalletResponse:
    """Получение кошелька пользователя."""
    return await wallet_service.get(wallet_id, current_user.id)


@router.post('/', status_code=201, responses=responses(400, 409))
@limiter.limit(settings.rate_limit_auth)
@service_exception_handler('Ошибка при создании кошелька')
async def create_wallet(
    request: Request,
    data: WalletCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    wallet_service: Annotated[WalletService, Depends(get_wallet_service)],
) -> WalletResponse:
    """Создание нового кошелька."""
    return await wallet_service.create(current_user.id, data)


@router.put('/{wallet_id}', responses=responses(400, 404, 409))
@limiter.limit(settings.rate_limit_auth)
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


@router.delete('/{wallet_id}', responses=responses(400, 404))
@limiter.limit(settings.rate_limit_auth)
@service_exception_handler('Ошибка при удалении кошелька')
async def delete_wallet(
    request: Request,
    wallet_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    wallet_service: Annotated[WalletService, Depends(get_wallet_service)],
) -> WalletDeleteResponse:
    """Удаление кошелька."""
    return await wallet_service.delete(wallet_id, current_user.id)


@router.get('/assets/{asset_id}/transactions', responses=responses(404))
@limiter.limit(settings.rate_limit_auth)
@service_exception_handler('Ошибка при получении транзакций актива')
async def get_asset_transactions(
    request: Request,
    asset_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    asset_service: Annotated[WalletAssetService, Depends(get_wallet_asset_service)],
) -> list[TransactionResponse]:
    """Получение транзакций актива."""
    return await asset_service.get_transactions(asset_id, current_user.id)


@router.get('/assets/{asset_id}/distribution', responses=responses(404))
@limiter.limit(settings.rate_limit_auth)
@service_exception_handler('Ошибка при получении информации о распределении актива')
async def get_asset(
    request: Request,
    asset_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    asset_service: Annotated[WalletAssetService, Depends(get_wallet_asset_service)],
) -> dict:
    """Получение информации о распределении актива по портфелям."""
    return await asset_service.get_distribution(asset_id, current_user.id)
