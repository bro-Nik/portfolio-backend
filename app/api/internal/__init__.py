from fastapi import APIRouter

from .endpoints import tickers

internal_router = APIRouter(prefix='/internal')

internal_router.include_router(tickers.router)
