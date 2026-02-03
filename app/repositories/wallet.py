from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Wallet
from app.repositories.base import BaseRepository
from app.schemas import WalletCreate, WalletUpdate


class WalletRepository(BaseRepository[Wallet, WalletCreate, WalletUpdate]):
    """Репозиторий для работы с кошельками."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Wallet, session)

    async def get_many_by_user(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        *,
        include_assets: bool = False,
    ) -> list[Wallet]:
        """Получить кошельки пользователя."""
        return await self.get_many_by(
            Wallet.user_id == user_id,
            skip=skip,
            limit=limit,
            relations=('assets',) if include_assets else (),
        )

    async def get_by_id_and_user_with_assets(self, wallet_id: int, user_id: int) -> Wallet | None:
        """Получить кошелек пользователя с активами."""
        return await self.get_by(
            Wallet.id == wallet_id,
            Wallet.user_id == user_id,
            relations=('assets',),
        )
