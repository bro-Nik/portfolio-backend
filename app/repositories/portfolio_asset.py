from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Asset, Portfolio
from app.repositories.base import BaseRepository

class AssetRepository(BaseRepository[Asset]):
    def __init__(self, ):
        super().__init__(Asset)

    async def get(
        self,
        db: AsyncSession,
        ticker_id: str,
        portfolio_id: int
    ) -> Asset:
        return await self.get_one(db, {'portfolio_id': portfolio_id, 'ticker_id': ticker_id})

    async def get_by_ticker_and_user(
        self,
        db: AsyncSession,
        ticker_id: str,
        user_id: int
    ) -> List[Asset]:
        """Получить все активы с указанным тикером для пользователя"""
        query = (
            select(Asset)
            .join(Asset.portfolio)
            .where(
                and_(
                    Asset.ticker_id == ticker_id,
                    Portfolio.user_id == user_id
                )
            )
            .options(selectinload(Asset.portfolio))
        )

        result = await db.execute(query)
        return result.scalars().all()

    async def get_asset_with_details(
        self,
        db: AsyncSession,
        asset_id: int,
        user_id: int
    ) -> Optional[Asset]:
        """Получить актив с детальной информацией (портфель + транзакции)"""
        query = (
            select(Asset)
            .join(Portfolio)
            .where(
                Asset.id == asset_id,
                Portfolio.user_id == user_id
            )
            .options(
                selectinload(Asset.portfolio),
                selectinload(Asset.transactions)
            )
        )

        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_portfolio_and_tickers(
        self,
        db: AsyncSession,
        portfolio_id: int,
        ticker_ids: List[str]
    ) -> List[Asset]:
        """Получить активы портфеля по списку тикеров"""
        if not ticker_ids:
            return []

        query = (
            select(Asset)
            .where(
                Asset.portfolio_id == portfolio_id,
                Asset.ticker_id.in_(ticker_ids)
            )
        )

        result = await db.execute(query)
        return result.scalars().all()
