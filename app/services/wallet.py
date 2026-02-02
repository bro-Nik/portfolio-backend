from typing import List
from app.repositories.wallet_asset import WalletAssetRepository
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.wallet_asset import WalletAssetService
from app.models import Transaction, Wallet, WalletAsset
from app.repositories.wallet import WalletRepository
from app.schemas import WalletEdit


class WalletService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.wallet_repo = WalletRepository(session)
        self.asset_service = WalletAssetService(session)
        self.asset_repo = WalletAssetRepository(session)

    async def get_user_wallets(self, user_id: int) -> List[Wallet]:
        """Получение всех кошельков пользователя"""
        return await self.wallet_repo.get_many_by_user(user_id, include_assets=True)

    async def get_user_wallet(self, wallet_id: int, user_id: int) -> Wallet:
        """Получение кошелька с проверкой прав доступа"""
        wallet = await self.wallet_repo.get_by_id_and_user_with_assets(wallet_id, user_id)

        if not wallet:
            raise ValueError("Кошелек не найден")

        return wallet

    async def create_wallet(self, user_id: int, wallet_data: WalletEdit) -> Wallet:
        """Создание нового кошелька"""
        wallet = Wallet(
            user_id=user_id,
            **wallet_data.model_dump()
        )

        # Добавляем в сессию
        wallet = await self.wallet_repo.create(wallet)

        await self.session.commit()
        await self.session.refresh(wallet)

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

        wallet = await self.wallet_repo.update(wallet_id, wallet_data)

        await self.session.commit()
        await self.session.refresh(wallet)
        return wallet

    async def delete_wallet(self, wallet_id: int, user_id: int) -> None:
        """Удаление кошелька"""
        await self.get_user_wallet(wallet_id, user_id)

        # ToDo Переделать (временно)
        relations = ('assets', 'transactions')
        wallet = await self.wallet_repo.get_by(Wallet.user_id == user_id, relations=relations)

        if wallet:
            for t in wallet.transactions:
                await self.session.delete(t)
            for a in wallet.assets:
                await self.session.delete(a)

        await self.wallet_repo.delete(wallet_id)

        await self.session.commit()

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

        return await self.asset_repo.get_many_by_tickers_and_wallet(
            ticker_ids, wallet_id
        )
