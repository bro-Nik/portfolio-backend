from typing import Optional
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel


class TransactionResponse(BaseModel):
    date: datetime
    ticker_id: str
    ticker2_id: Optional[str] = None
    quantity: Decimal
    quantity2: Optional[Decimal] = None
    price: Optional[Decimal] = None
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
    quantity: Decimal
    quantity2: Optional[Decimal] = None
    price: Optional[Decimal] = None
    price_usd: Optional[Decimal] = None
    type: str
    comment: Optional[str] = None
    wallet_id: Optional[int] = None
    wallet2_id: Optional[int] = None
    portfolio_id: Optional[int] = None
    portfolio2_id: Optional[int] = None
    order: bool = False


class TransactionUpdate(BaseModel):
    status: str
    amount: Optional[float] = None
