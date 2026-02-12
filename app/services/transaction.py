import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.models import PortfolioAsset, Transaction, WalletAsset
from app.repositories import TransactionRepository
from app.schemas import (
    TransactionCreate,
    TransactionCreateRequest,
    TransactionResponse,
    TransactionResponseWithAssets,
    TransactionUpdate,
    TransactionUpdateRequest,
)
from app.services.portfolio import PortfolioService
from app.services.portfolio_asset import PortfolioAssetService
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

    async def create(self, user_id: int, data: TransactionCreateRequest) -> TransactionResponseWithAssets:
        """Создание новой транзакции."""
        await self._validate_transaction_data(data)

        transaction_to_db = TransactionCreate(**data.model_dump(exclude_unset=True))
        transaction = await self.repo.create(transaction_to_db)
        await self.session.flush()

        # Уведомление сервисов о транзакции
        await self._notify_services(user_id, transaction)

        return await self._build_response_with_assets(transaction)

    async def update(
        self,
        user_id: int,
        transaction_id: int,
        data: TransactionUpdateRequest,
    ) -> TransactionResponseWithAssets:
        """Обновление транзакции."""
        await self._validate_transaction_data(data)
        transaction = await self._get_or_raise(transaction_id)

        # Уведомление сервисов о отмене транзакции
        await self._notify_services(user_id, transaction, cancel=True)

        transaction_to_db = TransactionUpdate(**data.model_dump(exclude_unset=True))
        updated_transaction = await self.repo.update(transaction.id, transaction_to_db)

        # Уведомление сервисов о транзакции
        await self._notify_services(user_id, updated_transaction)

        return await self._build_response_with_assets(updated_transaction, transaction)

    async def delete(self, user_id: int, transaction_id: int) -> TransactionResponseWithAssets:
        """Удаление транзакции."""
        transaction = await self._get_or_raise(transaction_id)

        # Уведомление сервисов о отмене транзакции
        await self._notify_services(user_id, transaction, cancel=True)

        await self.repo.delete(transaction_id)

        return await self._build_response_with_assets(transaction)

    async def convert_order_to_transaction(self, user_id: int, transaction_id: int) -> tuple[Transaction, Transaction]:
        """Конвертация ордера в транзакцию."""
        update_data = TransactionUpdate(order=False)
        return await self.update(user_id, transaction_id, update_data)

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

    async def _get_or_raise(self, transaction_id: int) -> Transaction:
        transaction = await self.repo.get(transaction_id)
        if not transaction:
            raise NotFoundError(f'Транзакция id={transaction_id} не найдена')
        return transaction

    async def _validate_transaction_data(self, data: TransactionCreateRequest) -> None:
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
        await self.portfolio_service.handle_transaction(user_id, t, cancel=cancel)
        await self.wallet_service.handle_transaction(user_id, t, cancel=cancel)

    @staticmethod
    def _validate_required_fields(
        data: TransactionCreateRequest | TransactionUpdateRequest,
        required_fields: list[str],
    ) -> None:
        missing = [field for field in required_fields if getattr(data, field, None) is None]
        if missing:
            raise ValidationError(f'Отсутствуют обязательные поля: {', '.join(missing)}')

    async def _build_response_with_assets(
        self,
        *transactions: Transaction,
    ) -> TransactionResponseWithAssets:
        portfolio_assets, wallet_assets = await asyncio.gather(
            self.portfolio_asset_service.get_affected(*transactions),
            self.wallet_asset_service.get_affected(*transactions),
        )

        return TransactionResponseWithAssets(
            transaction=transactions[0],
            portfolio_assets=portfolio_assets,
            wallet_assets=wallet_assets,
        )
