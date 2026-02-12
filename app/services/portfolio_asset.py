import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models import PortfolioAsset, Transaction
from app.repositories import PortfolioAssetRepository, TransactionRepository
from app.schemas import (
    PortfolioAssetCreate,
    PortfolioAssetCreateRequest,
    PortfolioAssetResponse,
)


class PortfolioAssetService:
    """Сервис для работы с активами портфелей."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = PortfolioAssetRepository(session)
        self.transaction_repo = TransactionRepository(session)

    async def create_asset(self, asset_data: PortfolioAssetCreateRequest) -> PortfolioAssetResponse:
        """Создать актив для портфеля."""
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

    async def get_asset_distribution(self, asset_id: int, user_id: int) -> tuple[PortfolioAsset, dict]:
        """Получение информации об распределении актива."""
        asset = await self._get_asset_or_raise(asset_id, user_id)

        # Расчет распределения по портфелям
        distribution = await self._calculate_portfolio_distribution(asset.ticker_id, user_id)
        return asset, distribution

    async def get_assets_by_portfolio_and_tickers(
        self,
        portfolio_id: int,
        ticker_ids: list[str],
    ) -> list[PortfolioAsset]:
        """Получить активы портфеля по тикерам."""
        return await self.repo.get_many_by_tickers_and_portfolio(ticker_ids, portfolio_id)

    async def _get_asset_or_raise(self, asset_id: int, user_id: int) -> PortfolioAsset:
        """Получить актив пользователя."""
        asset = await self.repo.get_by_id_and_user(asset_id, user_id)
        if not asset:
            raise NotFoundError(f'Актив id={asset_id} не найден')
        return asset

    async def _get_or_create_assets(
        self,
        *pairs: tuple[int | None, str | None],
    ) -> tuple[PortfolioAsset, ...]:
        tasks = [
            self.repo.get_or_create(portfolio_id=p_id, ticker_id=t_id)
            for p_id, t_id in pairs if p_id is not None and t_id is not None
        ]
        results = await asyncio.gather(*tasks)
        await self.session.flush()
        return tuple(results)

    async def _validate_create_data(self, data: PortfolioAssetCreateRequest) -> None:
        """Валидация данных для создания актива."""
        # Проверка, что актив еще не добавлен
        if await self.repo.get_by_ticker_and_portfolio(data.ticker_id, data.portfolio_id):
            raise ConflictError('Этот актив уже добавлен в портфель')

    async def _handle_trade(self, t: Transaction, direction: int) -> None:
        """Обработка торговой операции."""
        asset1, asset2 = await self._get_or_create_assets(
            (t.portfolio_id, t.ticker_id), (t.portfolio_id, t.ticker2_id),
        )

        handler = self._handle_trade_order if t.order else self._handle_trade_execution
        handler(asset1, t, direction, is_base_asset=True)
        handler(asset2, t, direction, is_base_asset=False)

    def _handle_trade_execution(
        self,
        asset: PortfolioAsset,
        t: Transaction,
        direction: int,
        *,
        is_base_asset: bool,
    ) -> None:
        """Обработка исполненной сделки."""
        if is_base_asset:
            asset.quantity += t.quantity * direction
            asset.amount += t.quantity * t.price_usd * direction
        elif not is_base_asset:
            asset.quantity -= t.quantity2 * direction
            # asset.amount -= t.quantity * t.price_usd * direction

    def _handle_trade_order(
        self,
        asset: PortfolioAsset,
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
        asset, = await self._get_or_create_assets((t.portfolio_id, t.ticker_id))
        asset.quantity += t.quantity * direction

    async def _handle_transfer(self, t: Transaction, direction: int) -> None:
        """Обработка перевода между портфелями."""
        asset1, asset2 = await self._get_or_create_assets(
            (t.portfolio_id, t.ticker_id), (t.portfolio2_id, t.ticker_id),
        )

        if asset1.quantity and t.quantity:
            amount = asset1.amount / asset1.quantity * t.quantity * direction
            asset1.amount += amount
            asset2.amount -= amount

        quantity = t.quantity * direction
        asset1.quantity += quantity
        asset2.quantity -= quantity

    async def _handle_input_output(self, t: Transaction, direction: int) -> None:
        """Обработка ввода-вывода."""
        asset, = await self._get_or_create_assets((t.portfolio_id, t.ticker_id))
        asset.quantity += t.quantity * direction

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
                'percentage_of_total': round(float(percentage), 2),
            })

        return {
            'total_quantity_all_portfolios': total_quantity,
            'total_amount_all_portfolios': total_amount,
            'portfolios': portfolio_distribution,
        }
