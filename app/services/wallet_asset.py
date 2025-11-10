from sqlalchemy.ext.asyncio import AsyncSession

from app import models
from app.repositories.wallet_asset import WalletAssetRepository


class WalletAssetService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.asset_repo = WalletAssetRepository()

    async def get_or_create(self, ticker_id: str, wallet_id: int) -> models.WalletAsset:
        asset = await self.asset_repo.get(self.db, ticker_id, wallet_id)

        if not asset:
            asset = await self._create(ticker_id, wallet_id)
        return asset

    async def _create(self, ticker_id: str, wallet_id: int) -> models.WalletAsset:
        new_asset = models.WalletAsset(ticker_id=ticker_id, wallet_id=wallet_id)
        asset = await self.asset_repo.create(self.db, new_asset)
        return asset
