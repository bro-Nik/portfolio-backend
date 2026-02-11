"""Портфели пользователя и их активы.

Все эндпоинты требуют валидный access token
"""

# TODO: Добавить responses для автодокументации


from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.core.exceptions import service_exception_handler
from app.core.rate_limit import limiter
from app.dependencies import (
    User,
    get_current_user,
    get_portfolio_asset_service,
    get_portfolio_service,
)
from app.schemas import (
    PortfolioAssetCreateRequest,
    PortfolioAssetDetailResponse,
    PortfolioCreateRequest,
    PortfolioDeleteResponse,
    PortfolioListResponse,
    PortfolioResponse,
    PortfolioUpdateRequest,
)
from app.services.portfolio import PortfolioService
from app.services.portfolio_asset import PortfolioAssetService

router = APIRouter(prefix='/portfolios', tags=['Portfolios'])


@router.get('/')
@limiter.limit('5/minute')
@service_exception_handler('Ошибка при получении портфелей')
async def get_user_portfolios(
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    portfolio_service: Annotated[PortfolioService, Depends(get_portfolio_service)],
) -> PortfolioListResponse:
    """Получение всех портфелей пользователя."""
    portfolios = await portfolio_service.get_portfolios(current_user.id)
    return PortfolioListResponse(portfolios=portfolios)


@router.get('/{portfolio_id}')
@limiter.limit('5/minute')
@service_exception_handler('Ошибка при получении портфеля')
async def get_user_portfolio(
    request: Request,
    portfolio_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    portfolio_service: Annotated[PortfolioService, Depends(get_portfolio_service)],
) -> PortfolioResponse:
    """Получение портфелея пользователя."""
    return await portfolio_service.get_portfolio(portfolio_id, current_user.id)


@router.post('/', status_code=201)
@limiter.limit('5/minute')
@service_exception_handler('Ошибка при создании портфеля')
async def create_portfolio(
    request: Request,
    portfolio_data: PortfolioCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    portfolio_service: Annotated[PortfolioService, Depends(get_portfolio_service)],
) -> PortfolioResponse:
    """Создание нового портфеля."""
    return await portfolio_service.create_portfolio(current_user.id, portfolio_data)


@router.put('/{portfolio_id}')
@limiter.limit('5/minute')
@service_exception_handler('Ошибка при изменении портфеля')
async def update_portfolio(
    request: Request,
    portfolio_id: int,
    portfolio_data: PortfolioUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    portfolio_service: Annotated[PortfolioService, Depends(get_portfolio_service)],
) -> PortfolioResponse:
    """Обновление портфеля."""
    return await portfolio_service.update_portfolio(portfolio_id, current_user.id, portfolio_data)


@router.delete('/{portfolio_id}')
@limiter.limit('5/minute')
@service_exception_handler('Ошибка при удалении портфеля')
async def delete_portfolio(
    request: Request,
    portfolio_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    portfolio_service: Annotated[PortfolioService, Depends(get_portfolio_service)],
) -> PortfolioDeleteResponse:
    """Удаление портфеля."""
    await portfolio_service.delete_portfolio(portfolio_id, current_user.id)
    return PortfolioDeleteResponse(portfolio_id=portfolio_id)


@router.post('/{portfolio_id}/assets', status_code=201)
@limiter.limit('5/minute')
@service_exception_handler('Ошибка при добавлении актива портфеля')
async def add_asset_to_portfolio(
    request: Request,
    portfolio_id: int,
    data: PortfolioAssetCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    portfolio_service: Annotated[PortfolioService, Depends(get_portfolio_service)],
    asset_service: Annotated[PortfolioAssetService, Depends(get_portfolio_asset_service)],
) -> PortfolioResponse:
    """Добавление актива в портфель."""
    data.portfolio_id=portfolio_id

    await asset_service.create_asset(data)
    return await portfolio_service.get_portfolio(portfolio_id, current_user.id)


@router.delete('/{portfolio_id}/assets/{asset_id}')
@limiter.limit('5/minute')
@service_exception_handler('Ошибка при удалении актива портфеля')
async def delete_asset_from_portfolio(
    request: Request,
    portfolio_id: int,
    asset_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    portfolio_service: Annotated[PortfolioService, Depends(get_portfolio_service)],
    asset_service: Annotated[PortfolioAssetService, Depends(get_portfolio_asset_service)],
) -> PortfolioResponse:
    """Удаление актива из портфеля."""
    await asset_service.delete_asset(asset_id)
    return await portfolio_service.get_portfolio(portfolio_id, current_user.id)


@router.get('/assets/{asset_id}')
@limiter.limit('5/minute')
@service_exception_handler('Ошибка при получении информации об активе')
async def get_asset(
    request: Request,
    asset_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    asset_service: Annotated[PortfolioAssetService, Depends(get_portfolio_asset_service)],
) -> PortfolioAssetDetailResponse:
    """Получение детальной информации об активе."""
    return await asset_service.get_asset_detail(asset_id, current_user.id)
