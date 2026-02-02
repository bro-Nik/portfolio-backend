from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Transaction, Asset
from app.repositories.portfolio_asset import AssetRepository
from app.schemas import TransactionCreate


class PortfolioAssetService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.asset_repo = AssetRepository(session)

    async def get(self, ticker_id: str, portfolio_id: int) -> Asset:
        return await self.asset_repo.get_by_ticker_and_portfolio(ticker_id, portfolio_id)

    async def get_or_create(self, ticker_id: str, portfolio_id: int) -> Asset:
        asset = await self.get(ticker_id, portfolio_id)

        if not asset:
            asset = await self._create(ticker_id, portfolio_id)
        return asset

    async def _create(self, ticker_id: str, portfolio_id: int) -> Asset:
        new_asset = Asset(ticker_id=ticker_id, portfolio_id=portfolio_id)
        asset = await self.asset_repo.create(new_asset)
        return asset

    async def handle_transaction(self, t: Transaction, cancel = False):
        """Обработка транзакции"""
        direction = t.get_direction(cancel)

        if t.type in ('Buy', 'Sell'):
            await self._handle_trade(t, direction)
        elif t.type == 'Earning':
            await self._handle_earning(t, direction)
        elif t.type in ('TransferIn', 'TransferOut'):
            await self._handle_transfer(t, direction)
        elif t.type in ('Input', 'Output'):
            await self._handle_input_output(t, direction)

    async def _handle_trade(self, t: Transaction, direction: int):
        """Обработка торговой операции"""
        # Получение или создание активов
        asset1 = await self.get_or_create(t.ticker_id, t.portfolio_id)
        asset2 = await self.get_or_create(t.ticker2_id, t.portfolio_id)

        if t.order:
            self._handle_trade_order(asset1, t, direction, True)
            self._handle_trade_order(asset2, t, direction, False)
        else:
            self._handle_trade_execution(asset1, t, direction, True)
            self._handle_trade_execution(asset2, t, direction, False)

    def _handle_trade_execution(self, asset: Asset, t: Transaction,
                                direction: int, is_primary: bool):
        """Обработка исполненной сделки"""
        if is_primary:
            # Базовый актив
            asset.quantity += t.quantity * direction
            asset.amount += t.quantity * t.price_usd * direction
        else:
            # Котируемый актив (валюта расчета)
            asset.quantity -= t.quantity2 * direction
            # asset.amount -= t.quantity * t.price_usd * direction

    def _handle_trade_order(self, asset: Asset, t: Transaction,
                            direction: int, is_primary: bool):
        """Обработка ордера"""
        if is_primary:
            # Базовый актив
            if t.type == 'Buy':
                asset.buy_orders += t.quantity * t.price_usd * direction
            elif t.type == 'Sell':
                asset.sell_orders -= t.quantity * direction
        else:
            # Котируемый актив (валюта расчета)
            if t.type == 'Buy':
                asset.sell_orders -= t.quantity2 * direction

    async def _handle_earning(self, t: Transaction, direction: int):
        """Обработка заработка"""
        # Получение или создание актива
        asset = await self.get_or_create(t.ticker_id, t.portfolio_id)
        asset.quantity += t.quantity * direction

    async def _handle_transfer(self, t: Transaction, direction: int):
        """Обработка перевода между портфелями"""
        # Получение или создание активов
        asset1 = await self.get_or_create(t.ticker_id, t.portfolio_id)
        asset2 = await self.get_or_create(t.ticker_id, t.portfolio2_id)

        amount = asset1.amount / asset1.quantity * t.quantity * direction
        asset1.amount += amount
        asset2.amount -= amount

        quantity = t.quantity * direction
        asset1.quantity += quantity
        asset2.quantity -= quantity


    async def _handle_input_output(self, t: Transaction, direction: int):
        """Обработка ввода-вывода"""
        # Получение или создание актива
        asset = await self.get_or_create(t.ticker_id, t.portfolio_id)

        asset.quantity += t.quantity * direction
