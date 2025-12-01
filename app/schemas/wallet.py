from pydantic import BaseModel
from typing import List, Optional


class WalletEdit(BaseModel):
    """Модель для создания и обновления кошелька"""
    name: str
    comment: Optional[str] = None


class WalletResponse(BaseModel):
    """Модель ответа для кошелька"""
    id: int
    name: str
    comment: Optional[str] = None
    assets: List['WalletAssetResponse'] = []

    class Config:
        from_attributes = True


class WalletListResponse(BaseModel):
    """Модель ответа для списка кошельков"""
    wallets: List[WalletResponse]


class WalletDeleteResponse(BaseModel):
    """Модель ответа для удаления"""
    wallet_id: int


class WalletAssetResponse(BaseModel):
    """Модель ответа для актива"""
    id: int
    ticker_id: str
    quantity: float
    buy_orders: float
    wallet_id: int

    class Config:
        from_attributes = True


class WalletToSellResponse(BaseModel):
    id: int
    name: str
    sort: float
    free: float
    subtext: str


class WalletToBuyResponse(BaseModel):
    id: int
    name: str

class ErrorResponse(BaseModel):
    message: str
