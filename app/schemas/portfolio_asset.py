from typing import List
from pydantic import BaseModel


class AssetResponse(BaseModel):
    """Модель ответа для актива"""
    id: int
    ticker_id: str
    quantity: float
    amount: float
    buy_orders: float
    portfolio_id: int

    class Config:
        from_attributes = True

class AssetEdit(BaseModel):
    portfolio_id: int
    ticker_id: str


class AssetDetailResponse(BaseModel):
    transactions: List[dict]
    distribution: dict
