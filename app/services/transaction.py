from sqlalchemy.ext.asyncio import AsyncSession

from app.services.portfolio import PortfolioService
from app.services.wallet import WalletService
from app.models import Transaction
from app.schemas import TransactionCreate, TransactionUpdate
from app.repositories.transaction import TransactionRepository


class TransactionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.transaction_repo = TransactionRepository()
        self.portfolio_service = PortfolioService(db)
        self.wallet_service = WalletService(db)

    async def create(self, user_id: int, transaction_data: TransactionCreate) -> Transaction:
        """Создание новой транзакции"""
        try:
            # Сохранение транзакции
            transaction = Transaction(**transaction_data.model_dump(exclude_unset=True))
            saved_transaction = await self.transaction_repo.create(self.db, transaction)

            # Уведомление сервисов о новой транзакции
            await self.portfolio_service.handle_transaction(user_id, transaction)
            await self.wallet_service.handle_transaction(user_id, transaction)

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
        """Обновление транзакции"""
        try:
            # Поиск транзакции
            transaction = await self.transaction_repo.get_by_id(self.db, transaction_id)
            if not transaction:
                raise ValueError(f"Transaction {transaction_id} not found")

            # Уведомление сервисов о отмене транзакции
            await self.portfolio_service.handle_transaction(user_id, transaction, cancel=True)
            await self.wallet_service.handle_transaction(user_id, transaction, cancel=True)

            # Обновление полей
            for field, value in update_data.model_dump(exclude_unset=True).items():
                setattr(transaction, field, value)

            # Обновление в репозитории
            updated_transaction = await self.transaction_repo.update(
                self.db, transaction.id, update_data
            )

            # Уведомление сервисов о транзакции
            await self.portfolio_service.handle_transaction(user_id, transaction)
            await self.wallet_service.handle_transaction(user_id, transaction)

            await self.db.commit()
            await self.db.refresh(updated_transaction)

            return updated_transaction

        except Exception as e:
            await self.db.rollback()
            raise e

    async def delete(self, user_id:int, transaction_id: int) -> dict:
        """Удаление транзакции"""
        try:
            transaction = await self.transaction_repo.get_by_id(self.db, transaction_id)
            if not transaction:
                raise ValueError(f"Transaction {transaction_id} not found")

            # Уведомление сервисов о отмене транзакции
            await self.portfolio_service.handle_transaction(user_id, transaction, cancel=True)
            await self.wallet_service.handle_transaction(user_id, transaction, cancel=True)

            # Сохраняем для получения связей
            rel = {
                'portfolio_id': transaction.portfolio_id,
                'portfolio2_id': transaction.portfolio2_id,
                'wallet_id': transaction.wallet_id,
                'wallet2_id': transaction.wallet2_id,
                }

            # Удаление
            await self.transaction_repo.delete(self.db, transaction_id)

            await self.db.commit()

            return rel

        except Exception as e:
            await self.db.rollback()
            raise e

    # async def convert_order_to_transaction(self,user_id:int, transaction_id: int) -> Transaction:
    #     """Конвертация ордера в транзакцию"""
    #     transaction = await self.transaction_repo.get_by_id(self.db, transaction_id)
    #     if not transaction:
    #         raise ValueError(f"Transaction {transaction_id} not found")
    #
    #     # Уведомление сервисов о отмене транзакции
    #     await self.portfolio_service.handle_transaction(user_id, transaction, cancel=True)
    #     await self.wallet_service.handle_transaction(user_id, transaction, cancel=True)
    #
    #     # Обновление полей
    #     transaction.order = False
    #     # transaction.date = datetime.now(timezone.utc)
    #
    #     # Уведомление сервисов о транзакции
    #     await self.portfolio_service.handle_transaction(user_id, transaction)
    #     await self.wallet_service.handle_transaction(user_id, transaction)
    #
    #     return await self.transaction_repo.update(transaction)
