from app.services.transaction import TransactionService
from app.services.wallet_asset import WalletAssetService
from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.exceptions import service_exception_handler
from app.dependencies.auth import get_current_user, User
from app.dependencies.wallet import get_wallet_service, get_wallet_asset_service
from app.services.wallet import WalletService
from app.schemas import (
    WalletListResponse,
    WalletResponse,
    WalletDeleteResponse,
    WalletAssetDetailResponse,
    ErrorResponse,
    WalletCreateRequest,
    WalletToBuyResponse,
    WalletToSellResponse,
    WalletUpdateRequest,
)


router = APIRouter(prefix="/api/wallets", tags=["wallets"])


@router.get("/", response_model=WalletListResponse)
@service_exception_handler('Ошибка при получении кошельков')
async def get_user_wallets(
    current_user: User = Depends(get_current_user),
    wallet_service: WalletService = Depends(get_wallet_service)
) -> WalletListResponse:
    """Получение всех кошельков пользователя"""
    wallets = await wallet_service.get_wallets(current_user.id)
    return WalletListResponse(wallets=wallets)


@router.post("/", response_model=WalletResponse)
@service_exception_handler('Ошибка при создании кошелька')
async def create_wallet(
    wallet_data: WalletCreateRequest,
    current_user: User = Depends(get_current_user),
    wallet_service: WalletService = Depends(get_wallet_service)
) -> WalletResponse:
    """Создание нового кошелька"""
    return await wallet_service.create_wallet(current_user.id, wallet_data)


@router.put("/{wallet_id}", response_model=WalletResponse)
@service_exception_handler('Ошибка при изменении кошелька')
async def update_wallet(
    wallet_id: int,
    wallet_data: WalletUpdateRequest,
    current_user: User = Depends(get_current_user),
    wallet_service: WalletService = Depends(get_wallet_service)
) -> WalletResponse:
    """Обновление кошелька"""
    return await wallet_service.update_wallet(wallet_id, current_user.id, wallet_data)


@router.delete("/{wallet_id}", response_model=WalletDeleteResponse)
@service_exception_handler('Ошибка при удалении кошелька')
async def delete_wallet(
    wallet_id: int,
    current_user: User = Depends(get_current_user),
    wallet_service: WalletService = Depends(get_wallet_service)
) -> WalletDeleteResponse:
    """Удаление кошелька"""
    await wallet_service.delete_wallet(wallet_id, current_user.id)
    return WalletDeleteResponse(wallet_id=wallet_id)


@router.get("/assets/{asset_id}", response_model=WalletAssetDetailResponse)
@service_exception_handler('Ошибка при получении информации об активе')
async def get_asset(
    asset_id: int,
    current_user: User = Depends(get_current_user),
    wallet_asset_service: WalletAssetService = Depends(get_wallet_asset_service)
) -> WalletAssetDetailResponse:
    """Получение детальной информации об активе"""
    asset_detail = await wallet_asset_service.get_asset_detail(asset_id, current_user.id)
    return WalletAssetDetailResponse(**asset_detail)
