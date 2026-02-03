from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db_session
from app.services.transaction import TransactionService


def get_transaction_service(session: AsyncSession = Depends(get_db_session)) -> TransactionService:
    return TransactionService(session)
