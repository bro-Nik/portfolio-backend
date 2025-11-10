from typing import List
from app.services.portfolio_asset import PortfolioAssetService
from sqlalchemy.ext.asyncio import AsyncSession

from app import models
from app.repositories.portfolio import PortfolioRepository
from app.repositories.portfolio_asset import AssetRepository
from app.schemas import PortfolioEdit


class PortfolioService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.portfolio_repo = PortfolioRepository()
        self.asset_repo = AssetRepository()
        self.asset_service = PortfolioAssetService(db)

    async def get_user_portfolios(self, user_id: int) -> List[models.Portfolio]:
        """Получение всех портфелей пользователя"""
        return await self.portfolio_repo.get_by_user_id(
            self.db, user_id, include_assets=True
        )

    async def get_user_portfolio(self, portfolio_id: int, user_id: int) -> models.Portfolio:
        """Получение портфеля с проверкой прав доступа"""
        portfolio = await self.portfolio_repo.get_by_id_with_assets(self.db, portfolio_id)

        if not portfolio or portfolio.user_id != user_id:
            raise ValueError("Портфель не найден")

        return portfolio

    async def create_portfolio(
        self,
        user_id: int,
        portfolio_data: PortfolioEdit
    ) -> models.Portfolio:
        """Создание нового портфеля"""
        # Проверка уникальности имени
        if await self.portfolio_repo.user_has_portfolio_with_name(self.db, user_id, portfolio_data.name):
            raise ValueError("Портфель с таким именем уже существует")

        portfolio = models.Portfolio(
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
    ) -> models.Portfolio:
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
        await self.portfolio_repo.delete(self.db, portfolio_id)

        await self.db.commit()

    async def add_asset(
        self,
        portfolio_id: int,
        user_id: int,
        ticker_id: str
    ) -> models.Portfolio:
        """Добавление актива в портфель"""
        portfolio = await self.get_user_portfolio(portfolio_id, user_id)

        # Проверка, что актив еще не добавлен
        if await self.asset_service.get(ticker_id, portfolio_id):
            raise ValueError("Этот актив уже добавлен в портфель")

        # Создание актива
        asset = models.Asset(
            portfolio_id=portfolio_id,
            ticker_id=ticker_id
        )

        await self.asset_repo.create(self.db, asset)
        await self.db.commit()
        await self.db.refresh(portfolio)

        return portfolio

    async def remove_asset(
        self,
        portfolio_id: int,
        user_id: int,
        asset_id: int
    ) -> models.Portfolio:
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
                "portfolio_id": transaction.portfolio_id,
                "wallet_id": transaction.wallet_id,
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
