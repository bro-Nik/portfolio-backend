from typing import List, Optional
from pydantic import BaseModel


class PortfolioEdit(BaseModel):
    """Модель для создания и обновления портфеля"""
    name: str
    market: str
    comment: Optional[str] = None


class PortfolioResponse(BaseModel):
    """Модель ответа для портфеля"""

    id: int
    name: str
    market: str
    comment: Optional[str] = None
    assets: List['AssetResponse'] = []

    class Config:
        from_attributes = True


class PortfolioListResponse(BaseModel):
    """Модель ответа для списка портфелей"""
    portfolios: List[PortfolioResponse]


class PortfolioDeleteResponse(BaseModel):
    """Модель ответа для удаления"""
    portfolio_id: int
