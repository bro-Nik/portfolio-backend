from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.wallet import WalletService
from app.services.wallet_asset import WalletAssetService


def get_wallet_service(db: AsyncSession = Depends(get_db)) -> WalletService:
    return WalletService(db)

def get_wallet_asset_service(db: AsyncSession = Depends(get_db)) -> WalletAssetService:
    return WalletAssetService(db)
