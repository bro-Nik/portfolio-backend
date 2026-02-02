from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.portfolio import PortfolioService
from app.services.wallet import WalletService
from app.services.transaction_analyzer import TransactionAnalyzer
from app.models import Asset, Transaction, WalletAsset
from app.schemas import TransactionCreate, TransactionUpdate
from app.repositories.transaction import TransactionRepository


class TransactionService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.transaction_repo = TransactionRepository(session)
        self.portfolio_service = PortfolioService(session)
        self.wallet_service = WalletService(session)
        self.analyzer = TransactionAnalyzer()

    async def create(
        self,
        user_id: int,
        transaction_data: TransactionCreate
    ) -> Transaction:
        """Создание новой транзакции"""
        try:
            # Сохранение транзакции
            transaction = Transaction(**transaction_data.model_dump(exclude_unset=True))
            saved_transaction = await self.transaction_repo.create(transaction)

            # Уведомление сервисов о новой транзакции
            await self.portfolio_service.handle_transaction(user_id, transaction)
            await self.wallet_service.handle_transaction(user_id, transaction)

            await self.session.commit()
            await self.session.refresh(saved_transaction)

            return saved_transaction

        except Exception as e:
            await self.session.rollback()
            raise e

    async def update(
        self,
        user_id: int,
        transaction_id: int,
        update_data: TransactionUpdate
    ) -> tuple[Transaction, Transaction]:
        """Обновление транзакции"""
        try:
            # Поиск транзакции
            transaction = await self.transaction_repo.get(transaction_id)
            if not transaction:
                raise ValueError(f"Transaction {transaction_id} not found")

            # Уведомление сервисов о отмене транзакции
            await self.portfolio_service.handle_transaction(user_id, transaction, cancel=True)
            await self.wallet_service.handle_transaction(user_id, transaction, cancel=True)

            # Обновление полей
            for field, value in update_data.model_dump(exclude_unset=True).items():
                setattr(transaction, field, value)

            # Обновление в репозитории
            updated_transaction = await self.transaction_repo.update(
                transaction.id, update_data
            )

            # Уведомление сервисов о транзакции
            await self.portfolio_service.handle_transaction(user_id, updated_transaction)
            await self.wallet_service.handle_transaction(user_id, updated_transaction)

            await self.session.commit()
            await self.session.refresh(updated_transaction)

            return updated_transaction, transaction

        except Exception as e:
            await self.session.rollback()
            raise e

    async def delete(self, user_id:int, transaction_id: int) -> Transaction:
        """Удаление транзакции"""
        try:
            transaction = await self.transaction_repo.get(transaction_id)
            if not transaction:
                raise ValueError(f"Transaction {transaction_id} not found")

            # Уведомление сервисов о отмене транзакции
            await self.portfolio_service.handle_transaction(user_id, transaction, cancel=True)
            await self.wallet_service.handle_transaction(user_id, transaction, cancel=True)

            # Удаление
            await self.transaction_repo.delete(transaction_id)

            await self.session.commit()

            return transaction

        except Exception as e:
            await self.session.rollback()
            raise e

    async def get_affected_portfolio_assets(
        self,
        user_id: int,
        transactions: List[Transaction]
    ) -> List[Asset]:
        """Получить измененные активы портфелей на основе транзакций"""
        if not transactions:
            return []

        # Собираем все затронутые активы из всех транзакций
        affected_assets_set = set()
        for t in transactions:
            affected = self.analyzer.get_affected_portfolio_assets(t)
            affected_assets_set.update(affected)

        if not affected_assets_set:
            return []

        # Группируем по portfolio_id и ticker_ids
        portfolio_assets_map = {}
        for portfolio_id, ticker_id in affected_assets_set:
            if portfolio_id not in portfolio_assets_map:
                portfolio_assets_map[portfolio_id] = []
            if ticker_id not in portfolio_assets_map[portfolio_id]:
                portfolio_assets_map[portfolio_id].append(ticker_id)

        # Получаем активы для каждого портфеля
        affected_assets = []
        for portfolio_id, ticker_ids in portfolio_assets_map.items():
            print(portfolio_id)
            assets = await self.portfolio_service.get_assets_by_portfolio_and_tickers(
                user_id, portfolio_id, ticker_ids
            )
            affected_assets.extend(assets)

        return affected_assets

    async def get_affected_wallet_assets(
        self,
        user_id: int,
        transactions: List[Transaction]
    ) -> List[WalletAsset]:
        """Получить измененные активы кошельков на основе транзакций"""
        if not transactions:
            return []

        # Собираем все затронутые активы из всех транзакций
        affected_assets_set = set()
        for t in transactions:
            affected = self.analyzer.get_affected_wallet_assets(t)
            affected_assets_set.update(affected)

        if not affected_assets_set:
            return []

        # Группируем по wallet_id и ticker_ids
        wallet_assets_map = {}
        for wallet_id, ticker_id in affected_assets_set:
            if wallet_id not in wallet_assets_map:
                wallet_assets_map[wallet_id] = []
            wallet_assets_map[wallet_id].append(ticker_id)

        # Получаем активы для каждого кошелька
        affected_assets = []
        for wallet_id, ticker_ids in wallet_assets_map.items():
            assets = await self.wallet_service.get_assets_by_wallet_and_tickers(
                user_id, wallet_id, ticker_ids
            )
            affected_assets.extend(assets)

        return affected_assets

    # async def convert_order_to_transaction(self,user_id:int, transaction_id: int) -> Transaction:
    #     """Конвертация ордера в транзакцию"""
    #     transaction = await self.transaction_repo.get_by_id(self.db, transaction_id)
    #     if not transaction:
    #         raise ValueError(f"Transaction {transaction_id} not found")
    #
    #     # Уведомление сервисов о отмене транзакции
    #     await self.portfolio_service.handle_transaction(user_id, transaction, cancel=True)
    #     await self.wallet_service.handle_transaction(user_id, transaction, cancel=True)
    #
    #     # Обновление полей
    #     transaction.order = False
    #     # transaction.date = datetime.now(timezone.utc)
    #
    #     # Уведомление сервисов о транзакции
    #     await self.portfolio_service.handle_transaction(user_id, transaction)
    #     await self.wallet_service.handle_transaction(user_id, transaction)
    #
    #     return await self.transaction_repo.update(transaction)
