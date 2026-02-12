from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class PortfolioAssetBase(BaseModel):
    """Базовые поля."""

    portfolio_id: int
    ticker_id: str


class PortfolioAssetCreateRequest(BaseModel):
    """Создание нового актива."""

    ticker_id: str
    portfolio_id: int


class PortfolioAssetCreate(PortfolioAssetBase):
    """Создание актива в БД."""


class PortfolioAssetUpdate(PortfolioAssetBase):
    """Обновление актива в БД."""


class PortfolioAssetResponse(PortfolioAssetBase):
    """Ответ с данными актива."""

    id: int
    quantity: Decimal
    amount: Decimal
    buy_orders: Decimal

    model_config = ConfigDict(from_attributes=True)
