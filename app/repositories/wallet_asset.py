from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.base import BaseRepository
from app.models import WalletAsset


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
