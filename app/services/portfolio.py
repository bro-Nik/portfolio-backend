from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.portfolio_asset import PortfolioAssetService
from app.models import Transaction, Portfolio, Asset
from app.repositories.portfolio import PortfolioRepository
from app.repositories.portfolio_asset import AssetRepository
from app.schemas import PortfolioEdit


class PortfolioService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.portfolio_repo = PortfolioRepository()
        self.asset_repo = AssetRepository()
        self.asset_service = PortfolioAssetService(db)

    async def get_user_portfolios(self, user_id: int, ids: list = []) -> List[Portfolio]:
        """Получение всех портфелей пользователя"""
        if ids:
            return await self.portfolio_repo.get_by_ids_and_user_id(
                self.db, user_id, ids, include_assets=True
            )

        return await self.portfolio_repo.get_by_user_id(
            self.db, user_id, include_assets=True
        )

    async def get_user_portfolio(self, portfolio_id: int, user_id: int) -> Portfolio:
        """Получение портфеля с проверкой прав доступа"""
        portfolio = await self.portfolio_repo.get_by_id_with_assets(self.db, portfolio_id)

        if not portfolio or portfolio.user_id != user_id:
            raise ValueError("Портфель не найден")

        return portfolio

    async def create_portfolio(
        self,
        user_id: int,
        portfolio_data: PortfolioEdit
    ) -> Portfolio:
        """Создание нового портфеля"""
        # Проверка уникальности имени
        if await self.portfolio_repo.user_has_portfolio_with_name(self.db, user_id, portfolio_data.name):
            raise ValueError("Портфель с таким именем уже существует")

        portfolio = Portfolio(
            user_id=user_id,
            **portfolio_data.model_dump()
        )

        # Добавляем в сессию
        portfolio = await self.portfolio_repo.create(self.db, portfolio)

        await self.db.commit()
        await self.db.refresh(portfolio)

        # Получаем портфель с загруженными связями
        portfolio = await self.get_user_portfolio(portfolio.id, user_id)

        return portfolio

    async def update_portfolio(
        self,
        portfolio_id: int,
        user_id: int,
        portfolio_data: PortfolioEdit
    ) -> Portfolio:
        """Обновление портфеля"""
        portfolio = await self.get_user_portfolio(portfolio_id, user_id)

        # Проверка уникальности имени (если имя изменилось)
        if portfolio_data.name != portfolio.name:
            if await self.portfolio_repo.user_has_portfolio_with_name(
                self.db, user_id, portfolio_data.name
            ):
                raise ValueError("Портфель с таким именем уже существует")

        # Обновление полей
        for field, value in portfolio_data.model_dump(exclude_unset=True).items():
            setattr(portfolio, field, value)

        portfolio = await self.portfolio_repo.update(self.db, portfolio_id, portfolio_data)

        await self.db.commit()
        await self.db.refresh(portfolio)
        return portfolio

    async def delete_portfolio(self, portfolio_id: int, user_id: int) -> None:
        """Удаление портфеля"""
        await self.get_user_portfolio(portfolio_id, user_id)

        # ToDo Переделать (временно)
        relationships = ['assets', 'transactions']
        portfolio = await self.portfolio_repo.get_one(self.db,  {'user_id': user_id}, relationships)

        for t in portfolio.transactions:
            await self.db.delete(t)
        for a in portfolio.assets:
            await self.db.delete(a)

        await self.portfolio_repo.delete(self.db, portfolio_id)

        await self.db.commit()

    async def add_asset(self, portfolio_id: int, user_id: int, ticker_id: str) -> Portfolio:
        """Добавление актива в портфель"""
        portfolio = await self.get_user_portfolio(portfolio_id, user_id)

        # Проверка, что актив еще не добавлен
        if await self.asset_service.get(ticker_id, portfolio_id):
            raise ValueError("Этот актив уже добавлен в портфель")

        # Создание актива
        asset = Asset(
            portfolio_id=portfolio_id,
            ticker_id=ticker_id
        )

        await self.asset_repo.create(self.db, asset)
        await self.db.commit()
        await self.db.refresh(portfolio)

        return portfolio

    async def remove_asset(self, portfolio_id: int, user_id: int, asset_id: int) -> Portfolio:
        """Удаление актива из портфеля"""
        portfolio = await self.get_user_portfolio(portfolio_id, user_id)

        # Проверка, что актив существует в портфеле
        asset = await self.asset_repo.get_by_id(self.db, asset_id)
        if not asset or asset.portfolio_id != portfolio_id:
            raise ValueError("Актив не найден в портфеле")

        await self.asset_repo.delete(self.db, asset_id)
        await self.db.commit()
        await self.db.refresh(portfolio)

        return portfolio


    async def get_asset_detail(self, asset_id: int, user_id: int) -> dict:
        """Получение детальной информации об активе"""
        # Загружаем актив с тикером и портфелем
        asset = await self.asset_repo.get_asset_with_details(self.db, asset_id, user_id)

        if not asset:
            raise ValueError("Актив не найден")

        # Подготовка транзакций
        asset_transactions = []
        for transaction in asset.transactions:
            asset_transactions.append({
                "id": transaction.id,
                "order": transaction.order,
                "portfolio_id": transaction.portfolio_id,
                "portfolio2_id": transaction.portfolio2_id,
                "wallet_id": transaction.wallet_id,
                # "wallet2_id": transaction.wallet2_id,
                "date": transaction.date,
                "ticker_id": transaction.ticker_id,
                "ticker2_id": transaction.ticker2_id,
                "quantity": transaction.quantity,
                "quantity2": transaction.quantity2,
                "price": transaction.price,
                "price_usd": transaction.price_usd,
                "type": transaction.type,
                "comment": transaction.comment,
            })

        # Расчет распределения по портфелям
        portfolio_distribution = await self._calculate_portfolio_distribution(
            asset.ticker_id, user_id
        )

        return {
            "transactions": asset_transactions,
            "distribution": portfolio_distribution
        }

    async def _calculate_portfolio_distribution(self, ticker_id: str, user_id: int) -> dict:
        """Расчет распределения актива по портфелям"""
        assets = await self.asset_repo.get_by_ticker_and_user(self.db, ticker_id, user_id)

        total_quantity = sum(asset.quantity for asset in assets)
        total_amount = sum(asset.amount for asset in assets)

        portfolio_distribution = []
        for asset in assets:
            percentage = (asset.quantity / total_quantity * 100) if total_quantity > 0 else 0
            portfolio_distribution.append({
                "portfolio_id": asset.portfolio.id,
                "portfolio_name": asset.portfolio.name,
                "quantity": asset.quantity,
                "amount": asset.amount,
                "percentage_of_total": percentage
            })

        return {
            "total_quantity_all_portfolios": total_quantity,
            "total_amount_all_portfolios": total_amount,
            "portfolios": portfolio_distribution
        }

    async def handle_transaction(self, user_id: int, t: Transaction, cancel = False):
        """Обработка транзакции"""
        if not t.portfolio_id:
            return

        if t.type in ('Buy', 'Sell'):
            await self._handle_trade(user_id, t)
        elif t.type == 'Earning':
            await self._handle_earning(user_id, t)
        elif t.type in ('TransferIn', 'TransferOut'):
            await self._handle_transfer(user_id, t)
        elif t.type in ('Input', 'Output'):
            await self._handle_input_output(user_id, t)

        # Уведомление сервиса актива о новой транзакции
        await self.asset_service.handle_transaction(t, cancel)

    async def _handle_trade(self, user_id: int, t: Transaction):
        """Обработка торговой операции"""
        # Валидация портфеля
        await self.get_user_portfolio(t.portfolio_id, user_id)

    async def _handle_earning(self, user_id: int, t: Transaction):
        """Обработка заработка"""
        # Валидация портфеля
        await self.get_user_portfolio(t.portfolio_id, user_id)

    async def _handle_transfer(self, user_id: int, t: Transaction):
        """Обработка перевода между портфелями"""
        # Валидация исходного портфеля
        await self.get_user_portfolio(t.portfolio_id, user_id)

        # Валидация целевого портфеля
        await self.get_user_portfolio(t.portfolio2_id, user_id)

    async def _handle_input_output(self, user_id: int, t: Transaction):
        """Обработка ввода-вывода"""
        # Валидация портфеля
        await self.get_user_portfolio(t.portfolio_id, user_id)

    async def get_assets_by_portfolio_and_tickers(
        self,
        user_id: int,
        portfolio_id: int,
        ticker_ids: List[str]
    ) -> List[Asset]:
        """Получить активы портфеля по тикерам"""
        # Проверяем права на портфель
        await self.get_user_portfolio(portfolio_id, user_id)

        if not ticker_ids:
            return []

        return await self.asset_repo.get_by_portfolio_and_tickers(
            self.db, portfolio_id, ticker_ids
        )
