from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.portfolio import PortfolioService
from app.services.transaction import TransactionService


def get_portfolio_service(db: AsyncSession = Depends(get_db)) -> PortfolioService:
    return PortfolioService(db)

def get_portfolio_transaction_service(db: AsyncSession = Depends(get_db)) -> TransactionService:
    return TransactionService(db)
