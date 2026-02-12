import asyncio
import functools
import operator

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.models import PortfolioAsset, Transaction, WalletAsset
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
        await self._validate_transaction_data(transaction_data)

        transaction_to_db = TransactionCreate(**transaction_data.model_dump(exclude_unset=True))
        transaction = await self.repo.create(transaction_to_db)
        await self.session.flush()

        # Уведомление сервисов о транзакции
        await self._notify_services(user_id, transaction)

        return transaction

    async def update_transaction(
        self,
        user_id: int,
        transaction_id: int,
        update_data: TransactionUpdateRequest,
    ) -> tuple[Transaction, Transaction]:
        """Обновление транзакции."""
        await self._validate_transaction_data(update_data)

        transaction = await self._get_transaction_or_raise(transaction_id)

        # Уведомление сервисов о отмене транзакции
        await self._notify_services(user_id, transaction, cancel=True)

        transaction_to_db = TransactionUpdate(**update_data.model_dump(exclude_unset=True))
        updated_transaction = await self.repo.update(transaction.id, transaction_to_db)

        # Уведомление сервисов о транзакции
        await self._notify_services(user_id, updated_transaction)

        return updated_transaction, transaction

    async def delete_transaction(self, user_id: int, transaction_id: int) -> Transaction:
        """Удаление транзакции."""
        transaction = await self._get_transaction_or_raise(transaction_id)

        # Уведомление сервисов о отмене транзакции
        await self._notify_services(user_id, transaction, cancel=True)

        await self.repo.delete(transaction_id)
        return transaction

    async def convert_order_to_transaction(
        self,
        user_id: int,
        transaction_id: int,
    ) -> tuple[Transaction, Transaction]:
        """Конвертация ордера в транзакцию."""
        update_data = TransactionUpdate(order=False)
        return await self.update_transaction(user_id, transaction_id, update_data)

    async def get_affected_portfolio_assets(
        self,
        transactions: tuple[Transaction, ...],
    ) -> list[PortfolioAssetResponse]:
        """Получить измененные активы портфелей на основе транзакций."""
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

    async def get_asset_transactions(
        self,
        asset: PortfolioAsset | WalletAsset,
    ) -> list[TransactionResponse]:
        """Получить транзакции портфеля."""
        if isinstance(asset, PortfolioAsset):
            transactions = await self.repo.get_many_by_ticker_and_portfolio(
                asset.ticker_id, asset.portfolio_id,
            )
        else:
            transactions = await self.repo.get_many_by_ticker_and_wallet(
                asset.ticker_id, asset.wallet_id,
            )
        return [TransactionResponse.model_validate(t) for t in transactions]

    async def _get_transaction_or_raise(self, transaction_id: int) -> Transaction:
        """Получить транзакцию или выбросить исключение."""
        transaction = await self.repo.get(transaction_id)
        if not transaction:
            raise NotFoundError(f'Транзакция id={transaction_id} не найдена')
        return transaction

    async def _validate_transaction_data(self, data: TransactionCreateRequest) -> None:
        """Валидация данных транзакции."""
        if data.type in ('Buy', 'Sell'):
            required = ['portfolio_id', 'wallet_id', 'ticker_id', 'ticker2_id', 'quantity']
            self._validate_required_fields(data, required)

        elif data.type == 'Earning':
            required = ['portfolio_id', 'wallet_id', 'ticker_id', 'quantity']
            self._validate_required_fields(data, required)

        elif data.type in ('TransferIn', 'TransferOut'):
            if data.portfolio_id:
                required = ['portfolio_id', 'portfolio2_id', 'ticker_id', 'quantity']
            else:
                required = ['wallet_id', 'wallet2_id', 'ticker_id', 'quantity']
            self._validate_required_fields(data, required)

        elif data.type in ('Input', 'Output'):
            if data.portfolio_id:
                required = ['portfolio_id', 'ticker_id', 'quantity']
            else:
                required = ['wallet_id', 'ticker_id', 'quantity']
            self._validate_required_fields(data, required)

        else:
            raise ValidationError(f'Неизвестный тип транзакции: {data.type}')

    async def _notify_services(self, user_id: int, t: Transaction, *, cancel: bool = False) -> None:
        """Уведомление сервисов о транзакции."""
        await self.portfolio_service.handle_transaction(user_id, t, cancel=cancel)
        await self.wallet_service.handle_transaction(user_id, t, cancel=cancel)

    @staticmethod
    def _validate_required_fields(
        data: TransactionCreateRequest | TransactionUpdateRequest,
        required_fields: list[str],
    ) -> None:
        """Проверка обязательных полей."""
        missing = [field for field in required_fields if getattr(data, field, None) is None]
        if missing:
            raise ValidationError(f'Отсутствуют обязательные поля: {', '.join(missing)}')
