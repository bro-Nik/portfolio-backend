"""Портфели пользователя и их активы.

Все эндпоинты требуют валидный access token
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.core.exceptions import service_exception_handler
from app.core.rate_limit import limiter
from app.core.responses import responses
from app.dependencies import (
    User,
    get_current_user,
    get_portfolio_asset_service,
    get_portfolio_service,
)
from app.schemas import (
    PortfolioAssetCreateRequest,
    PortfolioCreateRequest,
    PortfolioDeleteResponse,
    PortfolioListResponse,
    PortfolioResponse,
    PortfolioUpdateRequest,
    TransactionResponse,
)
from app.services import PortfolioAssetService, PortfolioService

router = APIRouter(prefix='/portfolios', tags=['Portfolios'], responses=responses(401, 429, 500))


@router.get('/')
@limiter.limit('5/minute')
@service_exception_handler('Ошибка при получении портфелей')
async def get_user_portfolios(
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    portfolio_service: Annotated[PortfolioService, Depends(get_portfolio_service)],
) -> PortfolioListResponse:
    """Получение всех портфелей пользователя."""
    return await portfolio_service.get_many(current_user.id)


@router.get('/{portfolio_id}', responses=responses(404))
@limiter.limit('5/minute')
@service_exception_handler('Ошибка при получении портфеля')
async def get_user_portfolio(
    request: Request,
    portfolio_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    portfolio_service: Annotated[PortfolioService, Depends(get_portfolio_service)],
) -> PortfolioResponse:
    """Получение портфеля пользователя."""
    return await portfolio_service.get(portfolio_id, current_user.id)


@router.post('/', status_code=201, responses=responses(400, 409))
@limiter.limit('5/minute')
@service_exception_handler('Ошибка при создании портфеля')
async def create_portfolio(
    request: Request,
    data: PortfolioCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    portfolio_service: Annotated[PortfolioService, Depends(get_portfolio_service)],
) -> PortfolioResponse:
    """Создание нового портфеля."""
    return await portfolio_service.create(current_user.id, data)


@router.put('/{portfolio_id}', responses=responses(400, 404, 409))
@limiter.limit('5/minute')
@service_exception_handler('Ошибка при изменении портфеля')
async def update_portfolio(
    request: Request,
    portfolio_id: int,
    data: PortfolioUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    portfolio_service: Annotated[PortfolioService, Depends(get_portfolio_service)],
) -> PortfolioResponse:
    """Обновление портфеля."""
    return await portfolio_service.update(portfolio_id, current_user.id, data)


@router.delete('/{portfolio_id}', responses=responses(400, 404))
@limiter.limit('5/minute')
@service_exception_handler('Ошибка при удалении портфеля')
async def delete_portfolio(
    request: Request,
    portfolio_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    portfolio_service: Annotated[PortfolioService, Depends(get_portfolio_service)],
) -> PortfolioDeleteResponse:
    """Удаление портфеля."""
    return await portfolio_service.delete(portfolio_id, current_user.id)


@router.post('/{portfolio_id}/assets', status_code=201, responses=responses(400, 404, 409))
@limiter.limit('5/minute')
@service_exception_handler('Ошибка при добавлении актива портфеля')
async def add_asset_to_portfolio(
    request: Request,
    portfolio_id: int,
    data: PortfolioAssetCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    portfolio_service: Annotated[PortfolioService, Depends(get_portfolio_service)],
) -> PortfolioResponse:
    """Добавление актива в портфель."""
    return await portfolio_service.add_asset(portfolio_id, current_user.id, data)


@router.delete('/{portfolio_id}/assets/{asset_id}', responses=responses(400, 404))
@limiter.limit('5/minute')
@service_exception_handler('Ошибка при удалении актива портфеля')
async def delete_asset_from_portfolio(
    request: Request,
    portfolio_id: int,
    asset_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    portfolio_service: Annotated[PortfolioService, Depends(get_portfolio_service)],
) -> PortfolioResponse:
    """Удаление актива из портфеля."""
    return await portfolio_service.delete_asset(portfolio_id, current_user.id, asset_id)


@router.get('/assets/{asset_id}/transactions', responses=responses(404))
@limiter.limit('5/minute')
@service_exception_handler('Ошибка при получении транзакций актива')
async def get_asset_transactions(
    request: Request,
    asset_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    asset_service: Annotated[PortfolioAssetService, Depends(get_portfolio_asset_service)],
) -> list[TransactionResponse]:
    """Получение транзакций актива."""
    return await asset_service.get_transactions(asset_id, current_user.id)


@router.get('/assets/{asset_id}/distribution', responses=responses(404))
@limiter.limit('5/minute')
@service_exception_handler('Ошибка при получении информации о распределении актива')
async def get_asset_distribution(
    request: Request,
    asset_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    asset_service: Annotated[PortfolioAssetService, Depends(get_portfolio_asset_service)],
) -> dict:
    """Получение информации о распределении актива по портфелям."""
    return await asset_service.get_distribution(asset_id, current_user.id)
