from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class TransactionBase(BaseModel):
    """Базовые поля."""

    date: datetime
    ticker_id: str
    ticker2_id: str | None = None
    quantity: Decimal
    quantity2: Decimal | None = None
    price: Decimal | None = None
    price_usd: Decimal | None = None
    type: str
    comment: str | None = None
    wallet_id: int | None = None
    wallet2_id: int | None = None
    portfolio_id: int | None = None
    portfolio2_id: int | None = None
    order: bool | None = None


class TransactionResponse(TransactionBase):
    """Ответ с данными транзакции."""

    id: int

    model_config = ConfigDict(from_attributes=True)


class TransactionCreateRequest(TransactionBase):
    """Создание новой транзакции."""


class TransactionUpdateRequest(BaseModel):
    """Обновление транзакции."""

    status: str
    amount: Decimal | None = None


class TransactionCreate(TransactionBase):
    """Создание транзакции в БД."""


class TransactionUpdate(TransactionBase):
    """Создание транзакции в БД."""


class TransactionResponseWithAssets(BaseModel):
    """Ответ с детальными данными транзакции и затронутых активов."""

    success: bool = True
    message: str | None = None
    transaction: TransactionResponse | None = None
    portfolio_assets: list['PortfolioAssetResponse'] | None = None
    wallet_assets: list['WalletAssetResponse'] | None = None
