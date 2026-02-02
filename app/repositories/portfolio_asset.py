from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Asset, Portfolio
from app.repositories.base import BaseRepository
from app.schemas.portfolio_asset import AssetEdit


class AssetRepository(BaseRepository[Asset, AssetEdit, AssetEdit]):
    """Репозиторий для работы с активами портфелей."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Asset, session)

    async def get_by_ticker_and_portfolio(self, ticker_id: str, portfolio_id: int) -> Asset | None:
        """Получить актив портфеля по тикеру."""
        return await self.get_by(
            Asset.portfolio_id == portfolio_id,
            Asset.ticker_id == ticker_id,
        )

    async def get_many_by_ticker_and_user(self, ticker_id: str, user_id: int) -> list[Asset]:
        """Получить активы пользователя по тикеру."""
        return await self.get_many_by(
            Asset.ticker_id == ticker_id,
            Portfolio.user_id == user_id,
            relations=('portfolio',),
        )

    async def get_by_id_and_user_with_details(self, asset_id: int, user_id: int) -> Asset | None:
        """Получить актив пользователя с портфелем и транзакциями."""
        return await self.get_by(
            Asset.id == asset_id,
            Portfolio.user_id == user_id,
            relations=('portfolio', 'transactions'),
        )

    async def get_many_by_tickers_and_portfolio(
        self,
        ticker_ids: list[str],
        portfolio_id: int,
    ) -> list[Asset]:
        """Получить активы портфеля по списку тикеров."""
        if not ticker_ids:
            return []

        return await self.get_many_by(
            Asset.portfolio_id == portfolio_id,
            Asset.ticker_id.in_(ticker_ids),
        )
