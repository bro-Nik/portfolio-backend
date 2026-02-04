import asyncio
import functools
import operator

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models import Transaction
from app.repositories import TransactionRepository
from app.schemas import (
    PortfolioAssetResponse,
    TransactionCreate,
    TransactionCreateRequest,
    TransactionResponse,
    TransactionUpdate,
    TransactionUpdateRequest,
    WalletAssetResponse,
)
from app.services.portfolio import PortfolioService
from app.services.portfolio_asset import PortfolioAssetService
from app.services.transaction_analyzer import TransactionAnalyzer
from app.services.wallet import WalletService
from app.services.wallet_asset import WalletAssetService


class TransactionService:
    """Сервис для работы с транзакциями активов портфелей и кошельков."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = TransactionRepository(session)
        self.portfolio_service = PortfolioService(session)
        self.portfolio_asset_service = PortfolioAssetService(session)
        self.wallet_service = WalletService(session)
        self.wallet_asset_service = WalletAssetService(session)
        self.analyzer = TransactionAnalyzer()

    async def create_transaction(
        self,
        user_id: int,
        transaction_data: TransactionCreateRequest,
    ) -> TransactionResponse:
        """Создание новой транзакции."""
        transaction_to_db = TransactionCreate(**transaction_data.model_dump(exclude_unset=True))
        transaction = await self.repo.create(transaction_to_db)

        # Уведомление сервисов о новой транзакции
        await self.portfolio_service.handle_transaction(user_id, transaction)
        await self.wallet_service.handle_transaction(user_id, transaction)

        return transaction

    async def update_transaction(
        self,
        user_id: int,
        transaction_id: int,
        update_data: TransactionUpdateRequest,
    ) -> tuple[Transaction, Transaction]:
        """Обновление транзакции."""
        transaction = await self.repo.get(transaction_id)
        if not transaction:
            raise NotFoundError(f'Транзакция id={transaction_id} не найдена')

        # Уведомление сервисов о отмене транзакции
        await asyncio.gather(
            self.portfolio_service.handle_transaction(user_id, transaction, cancel=True),
            self.wallet_service.handle_transaction(user_id, transaction, cancel=True),
        )

        transaction_to_db = TransactionUpdate(**update_data.model_dump(exclude_unset=True))
        updated_transaction = await self.repo.update(transaction.id, transaction_to_db)

        # Уведомление сервисов о транзакции
        await asyncio.gather(
            self.portfolio_service.handle_transaction(user_id, updated_transaction),
            self.wallet_service.handle_transaction(user_id, updated_transaction),
        )

        return updated_transaction, transaction

    async def delete_transaction(self, user_id:int, transaction_id: int) -> Transaction:
        """Удаление транзакции."""
        transaction = await self.repo.get(transaction_id)
        if not transaction:
            raise NotFoundError(f'Транзакция id={transaction_id} не найдена')

        # Уведомление сервисов о отмене транзакции
        await asyncio.gather(
            self.portfolio_service.handle_transaction(user_id, transaction, cancel=True),
            self.wallet_service.handle_transaction(user_id, transaction, cancel=True),
        )

        await self.repo.delete(transaction_id)
        return transaction

    async def get_affected_portfolio_assets(
        self,
        transactions: tuple[Transaction, ...],
    ) -> list[PortfolioAssetResponse]:
        """Получить измененные активы портфелей на основе транзакций."""
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
        tasks = [
            self.portfolio_asset_service.get_assets_by_portfolio_and_tickers(p_id, t_ids)
            for p_id, t_ids in portfolio_assets_map.items()
        ]
        results = await asyncio.gather(*tasks)

        assets = functools.reduce(operator.iadd, results, [])
        return [PortfolioAssetResponse.model_validate(a) for a in assets]


    async def get_affected_wallet_assets(
        self,
        transactions: tuple[Transaction, ...],
    ) -> list[WalletAssetResponse]:
        """Получить измененные активы кошельков на основе транзакций."""
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
        tasks = [
            self.wallet_asset_service.get_assets_by_wallet_and_tickers(w_id, t_ids)
            for w_id, t_ids in wallet_assets_map.items()
        ]
        results = await asyncio.gather(*tasks)

        assets = functools.reduce(operator.iadd, results, [])
        return [WalletAssetResponse.model_validate(a) for a in assets]

    async def convert_order_to_transaction(
        self,
        user_id:int,
        transaction_id: int,
    ) -> tuple[Transaction, Transaction]:
        """Конвертация ордера в транзакцию."""
        update_data = TransactionUpdate(order=False)
        return await self.update_transaction(user_id, transaction_id, update_data)
