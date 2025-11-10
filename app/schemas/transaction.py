from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class TransactionResponse(BaseModel):
    date: datetime
    ticker_id: str
    ticker2_id: Optional[str] = None
    quantity: float
    quantity2: Optional[float] = None
    price: Optional[float] = None
    type: str
    comment: Optional[str] = None
    wallet_id: Optional[int] = None
    portfolio_id: Optional[int] = None
    order: bool

    class Config:
        from_attributes = True


class TransactionCreate(BaseModel):
    date: datetime
    ticker_id: str
    ticker2_id: Optional[str] = None
    quantity: float
    quantity2: Optional[float] = None
    price: Optional[float] = None
    price_usd: Optional[float] = None
    ticker2_price: Optional[float] = None
    type: str
    comment: Optional[str] = None
    wallet_id: Optional[int] = None
    portfolio_id: Optional[int] = None
    portfolio2_id: Optional[int] = None
    order: bool = False
    # asset_id: int


class TransactionUpdate(BaseModel):
    status: str
    amount: Optional[float] = None
