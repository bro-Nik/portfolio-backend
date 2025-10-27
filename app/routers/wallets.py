from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from pydantic import BaseModel

from app.dependencies.auth import get_current_user, User
from app import models, database

router = APIRouter(prefix="/api/wallets", tags=["wallets"])


class WalletEdit(BaseModel):
    """Модель для создания и обновления кошелька"""
    name: str
    comment: Optional[str] = None


class WalletResponse(BaseModel):
    """Модель ответа для кошелька"""
    id: int
    name: str
    comment: Optional[str] = None
    assets: List['AssetResponse'] = []

    class Config:
        from_attributes = True


class WalletListResponse(BaseModel):
    """Модель ответа для списка кошельков"""
    wallets: List[WalletResponse]


class WalletDeleteResponse(BaseModel):
    """Модель ответа для удаления"""
    wallet_id: int


class AssetResponse(BaseModel):
    """Модель ответа для актива"""
    id: int
    ticker_id: str
    quantity: float
    buy_orders: float

    class Config:
        from_attributes = True


def _prepare_asset_response(asset: models.WalletAsset) -> AssetResponse:
    """Подготовка данных актива для ответа"""
    return AssetResponse(
        id=asset.id,
        ticker_id=asset.ticker_id,
        quantity=asset.quantity,
        buy_orders=asset.buy_orders,
    )


def _prepare_wallet_response(
    wallet: models.Wallet,
    include_assets: bool = False
) -> WalletResponse:
    """Подготовка данных кошелька для ответа"""
    wallet_data = {
        "id": wallet.id,
        "name": wallet.name,
        "comment": wallet.comment,
        "assets": []
    }

    if include_assets and wallet.assets:
        wallet_data["assets"] = [
            _prepare_asset_response(asset) for asset in wallet.assets
        ]

    return WalletResponse(**wallet_data)


async def _get_user_wallet(
    wallet_id: int,
    user_id: int,
    db: AsyncSession,
    load_assets: bool = False
) -> models.Wallet:
    """Получение кошелька с проверкой прав доступа"""
    query = select(models.Wallet).where(
        models.Wallet.id == wallet_id,
        models.Wallet.user_id == user_id
    )

    if load_assets:
        query = query.options(
            selectinload(models.Wallet.assets)
            .selectinload(models.WalletAsset.ticker)
        )

    result = await db.execute(query)
    wallet = result.scalar_one_or_none()

    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Кошелек не найден"
        )

    return wallet


@router.get("/", response_model=WalletListResponse)
async def get_user_wallets(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(database.get_db)
) -> WalletListResponse:
    """Получение всех кошельков пользователя"""
    result = await db.execute(
        select(models.Wallet)
        .where(models.Wallet.user_id == current_user.id)
        .options(
            selectinload(models.Wallet.assets)
        )
    )

    wallets = result.scalars().all()

    wallets_data = [
        _prepare_wallet_response(wallet, include_assets=True)
        for wallet in wallets
    ]

    return WalletListResponse(wallets=wallets_data)


@router.post("/", response_model=WalletResponse)
async def create_wallet(
    wallet_data: WalletEdit,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(database.get_db)
) -> WalletResponse:
    """Создание нового кошелька"""
    wallet = models.Wallet(
        user_id=current_user.id,
        name=wallet_data.name,
        comment=wallet_data.comment
    )

    db.add(wallet)
    await db.commit()
    await db.refresh(wallet)

    return _prepare_wallet_response(wallet)


@router.put("/{wallet_id}", response_model=WalletResponse)
async def update_wallet(
    wallet_id: int,
    wallet_data: WalletEdit,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(database.get_db)
) -> WalletResponse:
    """Обновление кошелька"""
    wallet = await _get_user_wallet(wallet_id, current_user.id, db)

    # Обновляем поля
    wallet.name = wallet_data.name
    wallet.comment = wallet_data.comment

    await db.commit()
    await db.refresh(wallet)

    return _prepare_wallet_response(wallet)


@router.delete("/{wallet_id}", response_model=WalletDeleteResponse)
async def delete_wallet(
    wallet_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(database.get_db)
) -> WalletDeleteResponse:
    """Удаление кошелька пользователя"""
    wallet = await _get_user_wallet(wallet_id, current_user.id, db)

    # TODO: Добавить проверку на наличие активов при необходимости
    # if wallet.assets:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="Невозможно удалить кошелек с активами"
    #     )

    await db.delete(wallet)
    await db.commit()

    return WalletDeleteResponse(wallet_id=wallet_id)
