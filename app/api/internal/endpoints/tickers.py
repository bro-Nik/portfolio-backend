from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy import distinct, select, union_all
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rate_limit import limiter
from app.dependencies import get_db_session
from app.models import PortfolioAsset, WalletAsset

router = APIRouter(tags=['Internal | Tickers'])


@router.get('/all_used_tickers')
@limiter.limit('5/minute')
async def get_all_used_tickers(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list:
    """Получение всех используемых тикеров пользователями."""
    tickers = union_all(
        select(distinct(PortfolioAsset.ticker_id)),  # Тикеры из портфелей
        select(distinct(WalletAsset.ticker_id)),  # Тикеры из кошельков
    )

    result = await session.execute(tickers)
    return [row[0] for row in result.all() if row[0]]
