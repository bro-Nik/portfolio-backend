from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db_session
from app.services.portfolio import PortfolioService
from app.services.portfolio_asset import PortfolioAssetService


def get_portfolio_service(session: AsyncSession = Depends(get_db_session)) -> PortfolioService:
    """Зависимость для получения сервиса портфелей."""
    return PortfolioService(session)


def get_portfolio_asset_service(session: AsyncSession = Depends(get_db_session)) -> PortfolioAssetService:
    """Зависимость для получения сервиса активов портфелей."""
    return PortfolioAssetService(session)
