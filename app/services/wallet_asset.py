import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models import Transaction, WalletAsset
from app.repositories import WalletAssetRepository
from app.schemas import WalletAssetDetailResponse


class WalletAssetService:
    """Сервис для работы с активами кошельков."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = WalletAssetRepository(session)

    async def get_asset_detail(self, asset_id: int, user_id: int) -> WalletAssetDetailResponse:
        """Получение детальной информации об активе."""
        # Загружаем актив с тикером и кошельком
        asset = await self.repo.get_by_id_and_user_with_details(asset_id, user_id)

        if not asset:
            raise NotFoundError(f'Актив id={asset_id} не найден')

        # Подготовка транзакций
        transactions = [
            {
                'id': transaction.id,
                'order': transaction.order,
                'portfolio_id': transaction.portfolio_id,
                'portfolio2_id': transaction.portfolio2_id,
                'wallet_id': transaction.wallet_id,
                'wallet2_id': transaction.wallet2_id,
                'date': transaction.date,
                'ticker_id': transaction.ticker_id,
                'ticker2_id': transaction.ticker2_id,
                'quantity': transaction.quantity,
                'quantity2': transaction.quantity2,
                'price': transaction.price,
                'price_usd': transaction.price_usd,
                'type': transaction.type,
                'comment': transaction.comment,
            }
            for transaction in asset.transactions
        ]

        # Расчет распределения по кошелькам
        distribution = await self._calculate_wallet_distribution(asset.ticker_id, user_id)

        return WalletAssetDetailResponse(
            transactions=transactions,
            distribution=distribution,
        )

    async def _calculate_wallet_distribution(self, ticker_id: str, user_id: int) -> dict:
        """Расчет распределения актива по портфелям."""
        assets = await self.repo.get_many_by_ticker_and_user(ticker_id, user_id)

        total_quantity = sum(asset.quantity for asset in assets)

        wallet_distribution = []
        for asset in assets:
            percentage = (asset.quantity / total_quantity * 100) if total_quantity > 0 else 0
            wallet_distribution.append({
                'wallet_id': asset.wallet.id,
                'wallet_name': asset.wallet.name,
                'quantity': asset.quantity,
                'percentage_of_total': percentage,
            })

        return {
            'total_quantity_all_wallets': total_quantity,
            'wallets': wallet_distribution,
        }

    async def handle_transaction(self, t: Transaction, *, cancel: bool = False) -> None:
        """Обработка транзакции."""
        direction = t.get_direction(cancel)

        if t.type in ('Buy', 'Sell'):
            await self._handle_trade(t, direction)
        elif t.type == 'Earning':
            await self._handle_earning(t, direction)
        elif t.type in ('TransferIn', 'TransferOut'):
            await self._handle_transfer(t, direction)
        elif t.type in ('Input', 'Output'):
            await self._handle_input_output(t, direction)

    async def _handle_trade(self, t: Transaction, direction: int) -> None:
        """Обработка торговой операции."""
        asset1, asset2 = await asyncio.gather(
            self.repo.get_or_create(wallet_id=t.wallet_id, ticker_id=t.ticker_id),
            self.repo.get_or_create(wallet_id=t.wallet_id, ticker_id=t.ticker2_id),
        )

        handler = self._handle_trade_order if t.order else self._handle_trade_execution
        handler(asset1, t, direction, is_primary=True)
        handler(asset2, t, direction, is_primary=False)

    def _handle_trade_execution(
        self,
        asset: WalletAsset,
        t: Transaction,
        direction: int,
        *,
        is_primary: bool,
    ) -> None:
        """Обработка исполненной сделки."""
        if is_primary:
            # Базовый актив
            asset.quantity += t.quantity * direction
        else:
            # Котируемый актив (валюта расчета)
            asset.quantity -= t.quantity2 * direction

    def _handle_trade_order(
        self,
        asset: WalletAsset,
        t: Transaction,
        direction: int,
        *,
        is_primary: bool,
    ) -> None:
        """Обработка ордера."""
        if is_primary:
            # Базовый актив
            if t.type == 'Buy':
                asset.buy_orders += t.quantity * t.price_usd * direction
            elif t.type == 'Sell':
                asset.sell_orders -= t.quantity * direction
        # Котируемый актив (валюта расчета)
        elif t.type == 'Buy':
            asset.sell_orders -= t.quantity2 * direction

    async def _handle_earning(self, t: Transaction, direction: int) -> None:
        """Обработка заработка."""
        asset = await self.repo.get_or_create(wallet_id=t.wallet_id, ticker_id=t.ticker_id)
        asset.quantity += t.quantity * direction

    async def _handle_transfer(self, t: Transaction, direction: int) -> None:
        """Обработка перевода между кошельками."""
        if not (t.wallet_id and t.wallet2_id):
            return

        asset1, asset2 = await asyncio.gather(
            self.repo.get_or_create(wallet_id=t.wallet_id, ticker_id=t.ticker_id),
            self.repo.get_or_create(wallet_id=t.wallet2_id, ticker_id=t.ticker2_id),
        )

        quantity = t.quantity * direction
        asset1.quantity += quantity
        asset2.quantity -= quantity

    async def _handle_input_output(self, t: Transaction, direction: int) -> None:
        """Обработка ввода-вывода."""
        asset = await self.repo.get_or_create(wallet_id=t.wallet_id, ticker_id=t.ticker_id)
        asset.quantity += t.quantity * direction

    async def get_assets_by_wallet_and_tickers(
        self,
        wallet_id: int,
        ticker_ids: list[str],
    ) -> list[WalletAsset]:
        """Получить активы кошелька по тикерам."""
        if not ticker_ids:
            return []

        return await self.repo.get_many_by_tickers_and_wallet(ticker_ids, wallet_id)
