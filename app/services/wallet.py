from typing import List
from app.repositories.wallet_asset import WalletAssetRepository
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.wallet_asset import WalletAssetService
from app.models import Transaction, Wallet, WalletAsset
from app.repositories.wallet import WalletRepository
from app.schemas import WalletEdit


class WalletService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.wallet_repo = WalletRepository()
        self.asset_service = WalletAssetService(db)
        self.asset_repo = WalletAssetRepository()

    async def get_user_wallets(self, user_id: int, ids: list = []) -> List[Wallet]:
        """Получение всех кошельков пользователя"""
        if ids:
            return await self.wallet_repo.get_by_ids_and_user_id(
                self.db, user_id, ids, include_assets=True
            )

        return await self.wallet_repo.get_by_user_id(
            self.db, user_id, include_assets=True
        )

    async def get_user_wallet(self, wallet_id: int, user_id: int) -> Wallet:
        """Получение кошелька с проверкой прав доступа"""
        wallet = await self.wallet_repo.get_by_id_with_assets(self.db, wallet_id)

        if not wallet or wallet.user_id != user_id:
            raise ValueError("Кошелек не найден")

        return wallet

    async def create_wallet(self, user_id: int, wallet_data: WalletEdit) -> Wallet:
        """Создание нового кошелька"""
        wallet = Wallet(
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
    ) -> Wallet:
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

    async def handle_transaction(self, user_id: int, t: Transaction, cancel = False):
        """Обработка транзакции"""

        if t.type in ('Buy', 'Sell'):
            await self._handle_trade(user_id, t)
        elif t.type == 'Earning':
            await self._handle_earning(user_id, t)
        elif t.type in ('TransferIn', 'TransferOut'):
            # Портфельный перевод
            if not (t.wallet_id and t.wallet2_id):
                return

            await self._handle_transfer(user_id, t)
        elif t.type in ('Input', 'Output'):
            await self._handle_input_output(user_id, t)

        # Уведомление сервиса актива о новой транзакции
        await self.asset_service.handle_transaction(t, cancel)

    async def _handle_trade(self, user_id: int, t: Transaction):
        """Обработка торговой операции"""
        # Валидация кошелька
        await self.get_user_wallet(t.wallet_id, user_id)

    async def _handle_earning(self, user_id: int, t: Transaction):
        """Обработка заработка"""
        # Валидация кошелька
        await self.get_user_wallet(t.wallet_id, user_id)

    async def _handle_transfer(self, user_id: int, t: Transaction):
        """Обработка перевода между портфелями"""
        # Валидация исходного кошелька
        await self.get_user_wallet(t.wallet_id, user_id)

        # Валидация целевого кошелька
        await self.get_user_wallet(t.wallet2_id, user_id)

    async def _handle_input_output(self, user_id: int, t: Transaction):
        """Обработка ввода-вывода"""
        # Валидация кошелька
        await self.get_user_wallet(t.wallet_id, user_id)

    async def get_assets_by_wallet_and_tickers(
        self,
        user_id: int,
        wallet_id: int,
        ticker_ids: List[str]
    ) -> List[WalletAsset]:
        """Получить активы кошелька по тикерам"""
        # Проверяем права на кошелек
        await self.get_user_wallet(wallet_id, user_id)

        if not ticker_ids:
            return []

        return await self.asset_repo.get_by_wallet_and_tickers(
            self.db, wallet_id, ticker_ids
        )
