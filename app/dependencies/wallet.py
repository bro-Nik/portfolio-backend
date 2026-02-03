from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db_session
from app.services.wallet import WalletService
from app.services.wallet_asset import WalletAssetService


def get_wallet_service(session: AsyncSession = Depends(get_db_session)) -> WalletService:
    return WalletService(session)

def get_wallet_asset_service(session: AsyncSession = Depends(get_db_session)) -> WalletAssetService:
    return WalletAssetService(session)
