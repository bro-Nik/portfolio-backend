# TODO: API Key аутентификация


from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import distinct, select, union_all
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db_session
from app.models import Asset, WalletAsset

router = APIRouter(tags=['Admin'])


@router.get('/all_used_tickers')
async def get_all_used_tickers(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list:
    """Получение всех используемых тикеров пользователями."""
    tickers = union_all(
        select(distinct(Asset.ticker_id)),  # Тикеры из портфелей
        select(distinct(WalletAsset.ticker_id)),  # Тикеры из кошельков
    )

    result = await session.execute(tickers)
    return [row[0] for row in result.all() if row[0]]
