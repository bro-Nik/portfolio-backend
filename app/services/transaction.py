from app.repositories.portfolio import PortfolioRepository
from app.repositories.wallet import WalletRepository
from app.services.portfolio_asset import PortfolioAssetService
from app.services.portfolio import PortfolioService
from app.services.wallet import WalletService
from app.services.wallet_asset import WalletAssetService
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_
from sqlalchemy import select
from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime

from app.models import Transaction, Portfolio, Wallet
from app.schemas import TransactionCreate, TransactionUpdate
from app.repositories.transaction import TransactionRepository


class TransactionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.transaction_repo = TransactionRepository()
        # self.portfolio_repo = PortfolioRepository()
        # self.wallet_repo = WalletRepository()
        self.portfolio_service = PortfolioService(db)
        self.portfolio_asset_service = PortfolioAssetService(db)
        self.wallet_service = WalletService(db)
        self.wallet_asset_service = WalletAssetService(db)
        # self.ticker_repo = TickerRepository()
        # self.asset_repo = AssetRepository()

    def extract_calculation_fields(self, transaction_data: TransactionCreate) -> tuple[dict, Transaction]:
        """Извлекаем поля, используемые для расчетов"""
        fields = ['ticker2_price', 'portfolio2_id']

        data = transaction_data.model_dump()
        data_fields = {}
        for field in fields:
            data_fields[field] = data.pop(field, None)
        return data_fields, Transaction(**data)

    async def create(self, user_id: int, transaction_data: TransactionCreate, isRelatedTransactin:bool = False) -> Transaction:
        """Создание новой транзакции"""
        try:
            # Подготовка данных и транзакции
            transaction_data = await self._calculate_transaction(transaction_data)
            _, transaction = self.extract_calculation_fields(transaction_data)

            # Сохранение транзакции
            saved_transaction = await self.transaction_repo.create(self.db, transaction)

            # Обновление зависимостей
            await self._update_dependencies(transaction_data, user_id)

            # Обновление связанных транзакций
            if not isRelatedTransactin:
                await self._update_related_transaction(transaction_data, transaction, user_id)

            # Коммит всей транзакции
            await self.db.commit()
            await self.db.refresh(saved_transaction)

            return saved_transaction

        except Exception as e:
            await self.db.rollback()
            raise e

    async def update(
        self,
        user_id: int,
        transaction_id: int,
        update_data: TransactionUpdate
    ) -> Transaction:
        """Обновление транзакции с управлением транзакцией БД"""
        try:
            # Подготовка данных и транзакции
            transaction = await self.transaction_repo.get_by_id(self.db, transaction_id)
            if not transaction:
                raise ValueError(f"Transaction {transaction_id} not found")

            # Отмена предыдущих изменений
            await self._update_dependencies(self.db, transaction, cancel=True)

            # Обновление полей
            for field, value in update_data.model_dump(exclude_unset=True).items():
                setattr(transaction, field, value)

            # Перерасчет и валидация
            await self._calculate_transaction(transaction, update_data)

            # Обновление в репозитории (flush)
            updated_transaction = await self.transaction_repo.update(
                self.db, transaction, update_data
            )

            # Обновление зависимостей
            await self._update_dependencies(updated_transaction, user_id)

            # Обновление связанных транзакций
            await self._update_related_transaction(updated_transaction)

            # Коммит
            await self.db.commit()
            await self.db.refresh(updated_transaction)

            return updated_transaction

        except Exception as e:
            await self.db.rollback()
            raise e



    async def delete(self, user_id:int, transaction_id: int) -> None:
        """Удаление транзакции"""
        try:
            transaction = await self.transaction_repo.get_by_id(self.db, transaction_id)
            if not transaction:
                raise ValueError(f"Transaction {transaction_id} not found")

            # Отмена изменений
            await self._update_dependencies(transaction, user_id, cancel=True)

            # Удаление
            await self.transaction_repo.delete(self.db, transaction_id)

            # Коммит
            await self.db.commit()

        except Exception as e:
            await self.db.rollback()
            raise e

    async def convert_order_to_transaction(self, transaction_id: int) -> Transaction:
        """Конвертация ордера в транзакцию"""
        transaction = await self.transaction_repo.get_by_id(transaction_id)
        if not transaction:
            raise ValueError(f"Transaction {transaction_id} not found")
        
        # Отмена ордера
        await self._update_dependencies(transaction, cancel=True)
        
        # Обновление полей
        transaction.order = False
        transaction.date = datetime.now(timezone.utc)
        
        # Применение как транзакции
        await self._update_dependencies(transaction)
        
        return await self.transaction_repo.update(transaction)

    async def _calculate_transaction(self, transaction_data: TransactionCreate) -> TransactionCreate:
        """Расчет дополнительных полей транзакции"""

        # Определение направления
        direction = 1 if transaction_data.type in ('Buy', 'Input', 'TransferIn', 'Earning') else -1

        # Расчет для торговых операций
        if transaction_data.type in ('Buy', 'Sell'):
            # Расчет цены в USD
            transaction_data.price_usd = transaction_data.price * transaction_data.ticker2_price

            # Расчет quantity/quantity2
            transaction_data.quantity *= direction
            transaction_data.quantity2 *= direction * -1

        # Расчет для операций с кошельком
        elif transaction_data.type in ('Input', 'Output', 'Earning'):
            transaction_data.quantity *= direction

        # Расчет для трансферов
        elif transaction_data.type in ('TransferIn', 'TransferOut'):
            transaction_data.quantity *= direction

        return transaction_data

    async def _update_dependencies(
        self,
        transaction: TransactionCreate,
        user_id: int,
        cancel: bool = False) -> None:
        """Обновление зависимых активов"""
        direction = -1 if cancel else 1

        # Обработка по типам операций
        if transaction.type in ('Buy', 'Sell'):
            await self._handle_trade_operation(transaction, direction, user_id)
        elif transaction.type == 'Earning':
            await self._handle_earning_operation(transaction, direction, user_id)
        else:
            await self._handle_transfer_operation(transaction, direction, user_id)

    async def _handle_trade_operation(self, t: TransactionCreate, direction: int, user_id: int):
        """Обработка торговых операций"""

        # Валидация и получение портфеля с кошельком
        p = await self.portfolio_service.get_user_portfolio(t.portfolio_id, user_id)
        w = await self.wallet_service.get_user_wallet(t.wallet_id, user_id)

        # Получение или создание активов
        p_asset1 = await self.portfolio_asset_service.get_or_create(t.ticker_id, p.id)
        p_asset2 = await self.portfolio_asset_service.get_or_create(t.ticker2_id, p.id)
        w_asset1 = await self.wallet_asset_service.get_or_create(t.ticker_id, w.id)
        w_asset2 = await self.wallet_asset_service.get_or_create(t.ticker2_id, w.id)

        if not all([p_asset1, p_asset2, w_asset1, w_asset2]):
            return

        if t.order:
            # Логика для ордеров
            if t.type == 'Buy':
                p_asset1.buy_orders += t.quantity * t.price_usd * direction
                p_asset2.sell_orders -= t.quantity2 * direction
                w_asset1.buy_orders += t.quantity * t.price_usd * direction
                w_asset2.sell_orders -= t.quantity2 * direction
            elif t.type == 'Sell':
                w_asset1.sell_orders -= t.quantity * direction
                p_asset1.sell_orders -= t.quantity * direction
        else:
            # Логика для исполненных транзакций
            p_asset1.amount += t.quantity * t.price_usd * direction
            p_asset1.quantity += t.quantity * direction
            # p_asset2.amount += t.quantity2 * p_asset2.price * direction
            p_asset2.amount += t.quantity2 * direction
            p_asset2.quantity += t.quantity2 * direction

            w_asset1.quantity += t.quantity * direction
            w_asset2.quantity += t.quantity2 * direction

    async def _handle_earning_operation(self, t: TransactionCreate, direction: int, user_id: int):
        """Обработка операций заработка"""

        # Валидация и получение портфеля с кошельком
        p = await self.portfolio_service.get_user_portfolio(t.portfolio_id, user_id)
        w = await self.wallet_service.get_user_wallet(t.wallet_id, user_id)

        # Получение или создание активов
        p_asset = await self.portfolio_asset_service.get_or_create(t.ticker_id, p.id)
        w_asset = await self.wallet_asset_service.get_or_create(t.ticker_id, w.id)

        if not all([p_asset, w_asset]):
            return

        p_asset.quantity += t.quantity * direction
        w_asset.quantity += t.quantity * direction

    async def _handle_transfer_operation(self, t: TransactionCreate, direction: int, user_id: int):
        """Обработка операций перевода"""
        # Перевод между портфелями
        if t.portfolio2_id:
            # Валидация и получение портфелей
            p1 = await self.portfolio_service.get_user_portfolio(t.portfolio_id, user_id)
            # p2 = await self.portfolio_service.get_user_portfolio(t.portfolio2_id, user_id)

            # Получение или создание актива
            p1_asset = await self.portfolio_asset_service.get_or_create(t.ticker_id, p1.id)
            # p2_asset = await self.portfolio_asset_service.get_or_create(t.ticker_id, p2.id)

            # if not all([p1_asset, p2_asset]):
            #     return

            p1_asset.amount += t.quantity * direction
            p1_asset.quantity += t.quantity * direction
            # p2_asset.amount += t.quantity * direction
            # p2_asset.quantity += t.quantity * direction

        # Перевод между кошельками
        if t.wallet_id:
            # Валидация и получение кошелька
            w = self.wallet_service.get_user_wallet(t.wallet_id, user_id)

            # Получение или создание актива
            asset = await self.wallet_asset_service.get_or_create(t.ticker_id, w.id)

            if asset:
                asset.quantity += t.quantity * direction

    async def _update_related_transaction(
        self,
        transaction_data: TransactionCreate,
        t: Transaction,
        user_id: int,
        cancel: bool = False
    ) -> None:
        """Обновление связанных транзакций для трансферов"""
        if transaction_data.type not in ('TransferIn', 'TransferOut'):
            return

        if cancel:
            # Отмена связанной транзакции
            if t.related_transaction:
                t2 = t.related_transaction
                t.related_transaction = None
                t2.related_transaction = None
                await self.delete(t2.id, user_id)
        else:
            # Создание/обновление связанной транзакции
            # Валидация и получение портфеля
            print(f'transaction_data.portfolio2_id: {transaction_data.portfolio2_id}')
            p = await self.portfolio_service.get_user_portfolio(transaction_data.portfolio2_id, user_id)

            # Получение или создание актива
            asset = await self.portfolio_asset_service.get_or_create(transaction_data.ticker_id, p.id)

            if asset:
                t2 = t.related_transaction
                if not t2:
                    # Создание новой связанной транзакции
                    related_data = TransactionCreate(
                        type='TransferOut' if transaction_data.type == 'TransferIn' else 'TransferIn',
                        date=transaction_data.date,
                        quantity=transaction_data.quantity * -1,
                        wallet_id=transaction_data.wallet_id,
                        portfolio_id=transaction_data.portfolio2_id,
                        ticker_id=transaction_data.ticker_id
                    )
                    t2 = await self.create(user_id, related_data, True)
                    t.related_transaction = t2

                # Обновление связи
                t.related_transaction_id = t2.id
                t2.related_transaction_id = t.id
