from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Portfolio
from app.repositories.base import BaseRepository


class PortfolioRepository(BaseRepository[Portfolio]):
    def __init__(self):
        super().__init__(Portfolio)

    async def get_by_user_id(
        self,
        db: AsyncSession,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        include_assets: bool = False
    ) -> List[Portfolio]:
        """Получить портфели пользователя"""
        relationships = ['assets'] if include_assets else None
        return await self.get_all(db, skip, limit, {'user_id': user_id}, relationships)

    async def get_by_ids_and_user_id(
        self,
        db: AsyncSession,
        user_id: int,
        ids: List[int],
        include_assets: bool = False
    ) -> List[Portfolio]:
        """Получить портфели пользователя"""
        relationships = ['assets'] if include_assets else None
        return await self.get_by_ids(db, ids, {'user_id': user_id}, relationships)

    async def get_by_id_with_assets(self, db: AsyncSession, portfolio_id: int) -> Optional[Portfolio]:
        """Получить портфель с активами"""
        return await self.get_by_id(db, portfolio_id, ['assets'])

    async def user_has_portfolio_with_name(
        self,
        db: AsyncSession,
        user_id: int,
        name: str,
    ) -> bool:
        """Проверить, есть ли у пользователя портфель с таким именем"""
        return await self.exists(db, {'user_id': user_id, 'name':name})
