from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app import models
from app.repositories.wallet import WalletRepository
from app.schemas.wallet import WalletEdit


class WalletService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.wallet_repo = WalletRepository()

    async def get_user_wallets(self, user_id: int) -> List[models.Wallet]:
        """Получение всех кошельков пользователя"""
        return await self.wallet_repo.get_by_user_id(
            self.db, user_id, include_assets=True
        )

    async def get_user_wallet(self, wallet_id: int, user_id: int) -> models.Wallet:
        """Получение кошелька с проверкой прав доступа"""
        wallet = await self.wallet_repo.get_by_id_with_assets(self.db, wallet_id)

        if not wallet or wallet.user_id != user_id:
            raise ValueError("Кошелек не найден")

        return wallet

    async def create_wallet(
        self,
        user_id: int,
        wallet_data: WalletEdit
    ) -> models.Wallet:
        """Создание нового кошелька"""
        wallet = models.Wallet(
            user_id=user_id,
            **wallet_data.model_dump()
        )

        # Добавляем в сессию
        wallet = await self.wallet_repo.create(self.db, wallet)

        await self.db.commit()
        await self.db.refresh(wallet)

        # Получаем кошелек с загруженными связями
        wallet = await self.get_user_wallet(wallet.id, user_id)

        return wallet

    async def update_wallet(
        self,
        wallet_id: int,
        user_id: int,
        wallet_data: WalletEdit
    ) -> models.Wallet:
        """Обновление кошелька"""
        wallet = await self.get_user_wallet(wallet_id, user_id)

        # Обновление полей
        for field, value in wallet_data.model_dump(exclude_unset=True).items():
            setattr(wallet, field, value)

        wallet = await self.wallet_repo.update(self.db, wallet_id, wallet_data)

        await self.db.commit()
        await self.db.refresh(wallet)
        return wallet

    async def delete_wallet(self, wallet_id: int, user_id: int) -> None:
        """Удаление кошелька"""
        await self.get_user_wallet(wallet_id, user_id)
        await self.wallet_repo.delete(self.db, wallet_id)

        await self.db.commit()
