import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models import Transaction, WalletAsset
from app.repositories import TransactionRepository, WalletAssetRepository


class WalletAssetService:
    """Сервис для работы с активами кошельков."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = WalletAssetRepository(session)
        self.transaction_repo = TransactionRepository(session)

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

    async def get_asset_distribution(self, asset_id: int, user_id: int) -> tuple[WalletAsset, dict]:
        """Получение информации об распределении актива."""
        asset = await self._get_asset_or_raise(asset_id, user_id)

        # Расчет распределения по кошелькам
        distribution = await self._calculate_wallet_distribution(asset.ticker_id, user_id)
        return asset, distribution

    async def get_assets_by_wallet_and_tickers(
        self,
        wallet_id: int,
        ticker_ids: list[str],
    ) -> list[WalletAsset]:
        """Получить активы кошелька по тикерам."""
        return await self.repo.get_many_by_tickers_and_wallet(ticker_ids, wallet_id)

    async def _get_asset_or_raise(self, asset_id: int, user_id: int) -> WalletAsset:
        """Получить актив пользователя."""
        asset = await self.repo.get_by_id_and_user(asset_id, user_id)
        if not asset:
            raise NotFoundError(f'Актив id={asset_id} не найден')
        return asset

    async def _get_or_create_assets(
        self,
        *pairs: tuple[int | None, str | None],
    ) -> tuple[WalletAsset, ...]:
        tasks = [
            self.repo.get_or_create(wallet_id=w_id, ticker_id=t_id)
            for w_id, t_id in pairs if w_id is not None and t_id is not None
        ]
        results = await asyncio.gather(*tasks)
        await self.session.flush()
        return tuple(results)

    async def _handle_trade(self, t: Transaction, direction: int) -> None:
        """Обработка торговой операции."""
        asset1, asset2 = await self._get_or_create_assets(
            (t.wallet_id, t.ticker_id), (t.wallet_id, t.ticker2_id),
        )

        handler = self._handle_trade_order if t.order else self._handle_trade_execution
        handler(asset1, t, direction, is_base_asset=True)
        handler(asset2, t, direction, is_base_asset=False)

    def _handle_trade_execution(
        self,
        asset: WalletAsset,
        t: Transaction,
        direction: int,
        *,
        is_base_asset: bool,
    ) -> None:
        """Обработка исполненной сделки."""
        if is_base_asset:
            asset.quantity += t.quantity * direction
        elif not is_base_asset:
            asset.quantity -= t.quantity2 * direction

    def _handle_trade_order(
        self,
        asset: WalletAsset,
        t: Transaction,
        direction: int,
        *,
        is_base_asset: bool,
    ) -> None:
        """Обработка ордера."""
        if is_base_asset:
            if t.type == 'Buy':
                asset.buy_orders += t.quantity * t.price_usd * direction
            elif t.type == 'Sell':
                asset.sell_orders -= t.quantity * direction
        elif not is_base_asset and t.type == 'Buy':
            asset.sell_orders -= t.quantity2 * direction

    async def _handle_earning(self, t: Transaction, direction: int) -> None:
        """Обработка заработка."""
        asset, = await self._get_or_create_assets((t.wallet_id, t.ticker_id))
        asset.quantity += t.quantity * direction

    async def _handle_transfer(self, t: Transaction, direction: int) -> None:
        """Обработка перевода между кошельками."""
        asset1, asset2 = await self._get_or_create_assets(
            (t.wallet_id, t.ticker_id), (t.wallet2_id, t.ticker_id),
        )

        quantity = t.quantity * direction
        asset1.quantity += quantity
        asset2.quantity -= quantity

    async def _handle_input_output(self, t: Transaction, direction: int) -> None:
        """Обработка ввода-вывода."""
        asset, = await self._get_or_create_assets((t.wallet_id, t.ticker_id))
        asset.quantity += t.quantity * direction

    async def _calculate_wallet_distribution(self, ticker_id: str, user_id: int) -> dict:
        """Расчет распределения актива по кошелькам."""
        assets = await self.repo.get_many_by_ticker_and_user(ticker_id, user_id)

        total_quantity = sum(asset.quantity for asset in assets)

        wallet_distribution = []
        for asset in assets:
            percentage = (asset.quantity / total_quantity * 100) if total_quantity > 0 else 0
            wallet_distribution.append({
                'wallet_id': asset.wallet.id,
                'wallet_name': asset.wallet.name,
                'quantity': asset.quantity,
                'percentage_of_total': round(float(percentage), 2),
            })

        return {
            'total_quantity_all_wallets': total_quantity,
            'wallets': wallet_distribution,
        }
