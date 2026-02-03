from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db_session
from app.services.portfolio import PortfolioService


def get_portfolio_service(session: AsyncSession = Depends(get_db_session)) -> PortfolioService:
    return PortfolioService(session)
