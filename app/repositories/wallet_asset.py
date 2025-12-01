from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.repositories.base import BaseRepository
from app.models import Wallet, WalletAsset


class WalletAssetRepository(BaseRepository[WalletAsset]):
    def __init__(self, ):
        super().__init__(WalletAsset)

    async def get(
        self,
        db: AsyncSession,
        ticker_id: str,
        wallet_id: int
    ) -> WalletAsset:
        return await self.get_one(db, {'wallet_id': wallet_id, 'ticker_id': ticker_id})

    async def get_by_ticker_and_user(
        self,
        db: AsyncSession,
        ticker_id: str,
        user_id: int
    ) -> List[WalletAsset]:
        """Получить все активы с указанным тикером для пользователя"""
        query = (
            select(WalletAsset)
            .join(WalletAsset.wallet)
            .where(
                and_(
                    WalletAsset.ticker_id == ticker_id,
                    Wallet.user_id == user_id
                )
            )
            .options(selectinload(WalletAsset.wallet))
        )

        result = await db.execute(query)
        return result.scalars().all()

    async def get_asset_with_details(
        self,
        db: AsyncSession,
        asset_id: int,
        user_id: int
    ) -> Optional[WalletAsset]:
        """Получить актив с детальной информацией (кошелек + транзакции)"""
        query = (
            select(WalletAsset)
            .join(Wallet)
            .where(
                WalletAsset.id == asset_id,
                Wallet.user_id == user_id
            )
            .options(
                selectinload(WalletAsset.wallet),
                selectinload(WalletAsset.transactions)
            )
        )

        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_wallet_and_tickers(
        self,
        db: AsyncSession,
        wallet_id: int,
        ticker_ids: List[str]
    ) -> List[WalletAsset]:
        """Получить активы кошелька по списку тикеров"""
        if not ticker_ids:
            return []

        query = (
            select(WalletAsset)
            .where(
                WalletAsset.wallet_id == wallet_id,
                WalletAsset.ticker_id.in_(ticker_ids)
            )
        )

        result = await db.execute(query)
        return result.scalars().all()
