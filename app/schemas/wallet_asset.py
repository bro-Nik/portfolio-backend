from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class WalletAssetBase(BaseModel):
    """Базовые поля."""

    wallet_id: int
    ticker_id: str


class WalletAssetCreate(WalletAssetBase):
    """Создание актива в БД."""


class WalletAssetUpdate(WalletAssetBase):
    """Обновление актива в БД."""


class WalletAssetResponse(WalletAssetBase):
    """Ответ с данными актива."""

    id: int
    quantity: Decimal
    buy_orders: Decimal

    model_config = ConfigDict(from_attributes=True)


class WalletAssetDetailResponse(BaseModel):
    """Ответ с детальными данными актива."""

    transactions: list['TransactionResponse']
    distribution: dict


