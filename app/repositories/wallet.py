from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Wallet
from app.repositories.base import BaseRepository


class WalletRepository(BaseRepository[Wallet]):
    def __init__(self):
        super().__init__(Wallet)

    async def get_by_user_id(
        self,
        db: AsyncSession,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        include_assets: bool = False
    ) -> List[Wallet]:
        """Получить кошельки пользователя"""
        relationships = ['assets'] if include_assets else None
        return await self.get_all(db, skip, limit, {'user_id': user_id}, relationships)

    async def get_by_id_with_assets(self, db: AsyncSession, wallet_id: int) -> Optional[Wallet]:
        """Получить кошелек с активами"""
        return await self.get_by_id(db, wallet_id, ['assets'])
