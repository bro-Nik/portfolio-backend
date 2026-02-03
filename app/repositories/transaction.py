from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Transaction
from app.repositories.base import BaseRepository
from app.schemas.transaction import TransactionCreate, TransactionUpdate


class TransactionRepository(BaseRepository[Transaction, TransactionCreate, TransactionUpdate]):
    """Репозиторий для работы с транзакциями."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Transaction, session)
