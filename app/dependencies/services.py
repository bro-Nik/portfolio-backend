from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db_session
from app.services.portfolio import PortfolioService
from app.services.portfolio_asset import PortfolioAssetService
from app.services.transaction import TransactionService
from app.services.wallet import WalletService
from app.services.wallet_asset import WalletAssetService


def get_portfolio_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> PortfolioService:
    """Зависимость для получения сервиса портфелей."""
    return PortfolioService(session)


def get_portfolio_asset_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> PortfolioAssetService:
    """Зависимость для получения сервиса активов портфелей."""
    return PortfolioAssetService(session)


def get_wallet_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> WalletService:
    """Зависимость для получения сервиса кошельков."""
    return WalletService(session)


def get_wallet_asset_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> WalletAssetService:
    """Зависимость для получения сервиса активов кошельков."""
    return WalletAssetService(session)


def get_transaction_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> TransactionService:
    """Зависимость для получения сервиса транзакций."""
    return TransactionService(session)










