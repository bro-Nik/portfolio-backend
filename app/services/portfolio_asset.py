import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Asset, Transaction
from app.repositories import AssetRepository
from app.schemas import (
    PortfolioAssetCreate,
    PortfolioAssetCreateRequest,
    PortfolioAssetDetailResponse,
    PortfolioAssetResponse,
)


class PortfolioAssetService:
    """Сервис для работы с активами портфелей."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = AssetRepository(session)

    async def create_asset(self, asset_data: PortfolioAssetCreateRequest) -> PortfolioAssetResponse:
        """Создать актив для портфелья."""
        await self._validate_create_data(asset_data)

        asset_to_db = PortfolioAssetCreate(**asset_data.model_dump())

        asset = await self.repo.create(asset_to_db)
        await self.session.flush()
        return PortfolioAssetResponse.model_validate(asset)

    async def delete_asset(self, asset_id: int) -> bool:
        """Удалить актив портфеля."""
        return await self.repo.delete(asset_id)

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
            self.repo.get_or_create(portfolio_id=t.portfolio_id, ticker_id=t.ticker_id),
            self.repo.get_or_create(portfolio_id=t.portfolio_id, ticker_id=t.ticker2_id),
        )

        handler = self._handle_trade_order if t.order else self._handle_trade_execution
        handler(asset1, t, direction, is_primary=True)
        handler(asset2, t, direction, is_primary=False)

    def _handle_trade_execution(
        self,
        asset: Asset,
        t: Transaction,
        direction: int,
        *,
        is_primary: bool,
    ) -> None:
        """Обработка исполненной сделки."""
        if is_primary:
            # Базовый актив
            asset.quantity += t.quantity * direction
            asset.amount += t.quantity * t.price_usd * direction
        else:
            # Котируемый актив (валюта расчета)
            asset.quantity -= t.quantity2 * direction
            # asset.amount -= t.quantity * t.price_usd * direction

    def _handle_trade_order(
        self,
        asset: Asset,
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
        asset = await self.repo.get_or_create(portfolio_id=t.portfolio_id, ticker_id=t.ticker_id)
        asset.quantity += t.quantity * direction

    async def _handle_transfer(self, t: Transaction, direction: int) -> None:
        """Обработка перевода между портфелями."""
        asset1, asset2 = await asyncio.gather(
            self.repo.get_or_create(portfolio_id=t.portfolio_id, ticker_id=t.ticker_id),
            self.repo.get_or_create(portfolio_id=t.portfolio2_id, ticker_id=t.ticker2_id),
        )

        amount = asset1.amount / asset1.quantity * t.quantity * direction
        asset1.amount += amount
        asset2.amount -= amount

        quantity = t.quantity * direction
        asset1.quantity += quantity
        asset2.quantity -= quantity

    async def _handle_input_output(self, t: Transaction, direction: int) -> None:
        """Обработка ввода-вывода."""
        asset = await self.repo.get_or_create(portfolio_id=t.portfolio_id, ticker_id=t.ticker_id)
        asset.quantity += t.quantity * direction

    async def get_asset_detail(self, asset_id: int, user_id: int) -> PortfolioAssetDetailResponse:
        """Получение детальной информации об активе."""
        # Загружаем актив с тикером и портфелем
        asset = await self.repo.get_by_id_and_user_with_details(asset_id, user_id)

        if not asset:
            raise ValueError('Актив не найден')

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

        # Расчет распределения по портфелям
        distribution = await self._calculate_portfolio_distribution(asset.ticker_id, user_id)

        return PortfolioAssetDetailResponse(
            transactions=transactions,
            distribution=distribution,
        )

    async def _calculate_portfolio_distribution(self, ticker_id: str, user_id: int) -> dict:
        """Расчет распределения актива по портфелям."""
        assets = await self.repo.get_many_by_ticker_and_user(ticker_id, user_id)

        total_quantity = sum(asset.quantity for asset in assets)
        total_amount = sum(asset.amount for asset in assets)

        portfolio_distribution = []
        for asset in assets:
            percentage = (asset.quantity / total_quantity * 100) if total_quantity > 0 else 0
            portfolio_distribution.append({
                'portfolio_id': asset.portfolio.id,
                'portfolio_name': asset.portfolio.name,
                'quantity': asset.quantity,
                'amount': asset.amount,
                'percentage_of_total': percentage,
            })

        return {
            'total_quantity_all_portfolios': total_quantity,
            'total_amount_all_portfolios': total_amount,
            'portfolios': portfolio_distribution,
        }

    async def get_assets_by_portfolio_and_tickers(
        self,
        portfolio_id: int,
        ticker_ids: list[str],
    ) -> list[Asset]:
        """Получить активы портфеля по тикерам."""
        if not ticker_ids:
            return []

        return await self.repo.get_many_by_tickers_and_portfolio(ticker_ids, portfolio_id)

    async def _validate_create_data(self, data: PortfolioAssetCreateRequest) -> None:
        """Валидация данных для создания портфеля."""
        # Проверка, что актив еще не добавлен
        if await self.repo.get_by_ticker_and_portfolio(data.ticker_id, data.portfolio_id):
            raise ValueError('Этот актив уже добавлен в портфель')
