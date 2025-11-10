from sqlalchemy.ext.asyncio import AsyncSession

from app import models
from app.repositories.portfolio_asset import AssetRepository


class PortfolioAssetService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.asset_repo = AssetRepository()

    async def get(self, ticker_id: str, portfolio_id: int) -> models.Asset:
        return await self.asset_repo.get(self.db, ticker_id, portfolio_id)

    async def get_or_create(self, ticker_id: str, portfolio_id: int) -> models.Asset:
        asset = await self.get(ticker_id, portfolio_id)

        if not asset:
            asset = await self._create(ticker_id, portfolio_id)
        return asset

    async def _create(self, ticker_id: str, portfolio_id: int) -> models.Asset:
        new_asset = models.Asset(ticker_id=ticker_id, portfolio_id=portfolio_id)
        asset = await self.asset_repo.create(self.db, new_asset)
        return asset
