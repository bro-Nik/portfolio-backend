from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Portfolio, PortfolioAsset
from app.repositories.base import BaseRepository
from app.schemas import PortfolioAssetCreate, PortfolioAssetUpdate


class PortfolioAssetRepository(BaseRepository[PortfolioAsset, PortfolioAssetCreate, PortfolioAssetUpdate]):
    """Репозиторий для работы с активами портфелей."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(PortfolioAsset, session)

    async def get_by_ticker_and_portfolio(self, ticker_id: str, portfolio_id: int) -> PortfolioAsset | None:
        """Получить актив портфеля по тикеру."""
        return await self.get_by(
            PortfolioAsset.portfolio_id == portfolio_id,
            PortfolioAsset.ticker_id == ticker_id,
        )

    async def get_many_by_ticker_and_user(self, ticker_id: str, user_id: int) -> list[PortfolioAsset]:
        """Получить активы пользователя по тикеру."""
        portfolio_subq = select(Portfolio.id).where(Portfolio.user_id == user_id).scalar_subquery()

        return await self.get_many_by(
            PortfolioAsset.ticker_id == ticker_id,
            PortfolioAsset.portfolio_id.in_(portfolio_subq),
            relations=('portfolio',),
        )

    async def get_by_id_and_user(self, asset_id: int, user_id: int) -> PortfolioAsset | None:
        """Получить актив пользователя по ID."""
        portfolio_subq = select(Portfolio.id).where(Portfolio.user_id == user_id).scalar_subquery()

        return await self.get_by(
            PortfolioAsset.id == asset_id,
            PortfolioAsset.portfolio_id.in_(portfolio_subq),
        )

    async def get_many_by_tickers_and_portfolio(
        self,
        ticker_ids: list[str],
        portfolio_id: int,
    ) -> list[PortfolioAsset]:
        """Получить активы портфеля по списку тикеров."""
        return await self.get_many_by(
            PortfolioAsset.portfolio_id == portfolio_id,
            PortfolioAsset.ticker_id.in_(ticker_ids),
        )
