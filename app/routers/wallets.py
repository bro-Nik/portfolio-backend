from fastapi import APIRouter, Depends, HTTPException

from app.dependencies.auth import get_current_user, User
from app.dependencies.wallet import get_wallet_service
from app.services.wallet import WalletService
from app.schemas import (
    WalletListResponse,
    WalletResponse,
    WalletEdit,
    WalletDeleteResponse
)


router = APIRouter(prefix="/api/wallets", tags=["wallets"])


@router.get("/", response_model=WalletListResponse)
async def get_user_wallets(
    current_user: User = Depends(get_current_user),
    wallet_service: WalletService = Depends(get_wallet_service)
) -> WalletListResponse:
    """Получение всех кошельков пользователя"""
    try:
        wallets = await wallet_service.get_user_wallets(current_user.id)
        return WalletListResponse(wallets=wallets)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=WalletResponse)
async def create_wallet(
    wallet_data: WalletEdit,
    current_user: User = Depends(get_current_user),
    wallet_service: WalletService = Depends(get_wallet_service)
) -> WalletResponse:
    """Создание нового кошелька"""
    try:
        wallet = await wallet_service.create_wallet(current_user.id, wallet_data)
        return wallet
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{wallet_id}", response_model=WalletResponse)
async def update_wallet(
    wallet_id: int,
    wallet_data: WalletEdit,
    current_user: User = Depends(get_current_user),
    wallet_service: WalletService = Depends(get_wallet_service)
) -> WalletResponse:
    """Обновление кошелька"""
    try:
        wallet = await wallet_service.update_wallet(
            wallet_id, current_user.id, wallet_data
        )
        return wallet
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{wallet_id}", response_model=WalletDeleteResponse)
async def delete_wallet(
    wallet_id: int,
    current_user: User = Depends(get_current_user),
    wallet_service: WalletService = Depends(get_wallet_service)
) -> WalletDeleteResponse:
    """Удаление кошелька"""
    try:
        await wallet_service.delete_wallet(wallet_id, current_user.id)
        return WalletDeleteResponse(wallet_id=wallet_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
