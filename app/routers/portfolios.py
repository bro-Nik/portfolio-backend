from typing import List

from app.schemas.portfolio import PortfolioCreateRequest, PortfolioUpdateRequest
from app.schemas.portfolio_asset import PortfolioAssetCreateRequest
from fastapi import APIRouter, Depends, HTTPException, Query
from app.services.portfolio_asset import PortfolioAssetService

from app.core.exceptions import service_exception_handler
from app.dependencies.auth import get_current_user, User
from app.dependencies import get_portfolio_service, get_portfolio_asset_service
from app.services.portfolio import PortfolioService
from app.schemas import (
    PortfolioResponse,
    PortfolioListResponse,
    PortfolioDeleteResponse,
    PortfolioAssetDetailResponse,
)


router = APIRouter(prefix="/api/portfolios", tags=["portfolios"])


@router.get("/", response_model=PortfolioListResponse)
@service_exception_handler('Ошибка при получении портфелей')
async def get_user_portfolios(
    current_user: User = Depends(get_current_user),
    portfolio_service: PortfolioService = Depends(get_portfolio_service)
) -> PortfolioListResponse:
    """Получение всех портфелей пользователя"""
    portfolios = await portfolio_service.get_portfolios(current_user.id)
    return PortfolioListResponse(portfolios=portfolios)


@router.get("/", response_model=PortfolioListResponse)
@service_exception_handler('Ошибка при получении портфелей')
async def get_user_portfolios_by_ids(
    ids: List[int] = Query(..., description="Список ID портфелей"),
    current_user: User = Depends(get_current_user),
    portfolio_service: PortfolioService = Depends(get_portfolio_service)
) -> PortfolioListResponse:
    """Получение портфелей пользователя по списку id"""
    portfolios = await portfolio_service.get_portfolios(current_user.id, ids)
    return PortfolioListResponse(portfolios=portfolios)


@router.post("/", response_model=PortfolioResponse)
@service_exception_handler('Ошибка при создании портфеля')
async def create_portfolio(
    portfolio_data: PortfolioCreateRequest,
    current_user: User = Depends(get_current_user),
    portfolio_service: PortfolioService = Depends(get_portfolio_service)
) -> PortfolioResponse:
    """Создание нового портфеля"""
    return await portfolio_service.create_portfolio(current_user.id, portfolio_data)


@router.put("/{portfolio_id}", response_model=PortfolioResponse)
@service_exception_handler('Ошибка при изменении портфеля')
async def update_portfolio(
    portfolio_id: int,
    portfolio_data: PortfolioUpdateRequest,
    current_user: User = Depends(get_current_user),
    portfolio_service: PortfolioService = Depends(get_portfolio_service)
) -> PortfolioResponse:
    """Обновление портфеля"""
    return await portfolio_service.update_portfolio(
        portfolio_id, current_user.id, portfolio_data
    )


@router.delete("/{portfolio_id}", response_model=PortfolioDeleteResponse)
@service_exception_handler('Ошибка при удалении портфеля')
async def delete_portfolio(
    portfolio_id: int,
    current_user: User = Depends(get_current_user),
    portfolio_service: PortfolioService = Depends(get_portfolio_service)
) -> PortfolioDeleteResponse:
    """Удаление портфеля"""
    await portfolio_service.delete_portfolio(portfolio_id, current_user.id)
    return PortfolioDeleteResponse(portfolio_id=portfolio_id)


@router.post("/{portfolio_id}/assets", response_model=PortfolioResponse)
@service_exception_handler('Ошибка при добавлении актива портфеля')
async def add_asset_to_portfolio(
    portfolio_id: int,
    data: PortfolioAssetCreateRequest,
    current_user: User = Depends(get_current_user),
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
    asset_service: PortfolioAssetService = Depends(get_portfolio_asset_service)
) -> PortfolioResponse:
    """Добавление актива в портфель"""
    data.portfolio_id=portfolio_id
    await asset_service.create_asset(data)

    return await portfolio_service.get_portfolio(portfolio_id, current_user.id)


@router.delete("/{portfolio_id}/assets/{asset_id}", response_model=PortfolioResponse)
@service_exception_handler('Ошибка при удалении актива портфеля')
async def delete_asset_from_portfolio(
    portfolio_id: int,
    asset_id: int,
    current_user: User = Depends(get_current_user),
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
    asset_service: PortfolioAssetService = Depends(get_portfolio_asset_service)
) -> PortfolioResponse:
    """Удаление актива из портфеля"""
    await asset_service.delete_asset(asset_id)
    return await portfolio_service.get_portfolio(portfolio_id, current_user.id)


@router.get("/assets/{asset_id}", response_model=PortfolioAssetDetailResponse)
@service_exception_handler('Ошибка при получении информации об активе')
async def get_asset(
    asset_id: int,
    current_user: User = Depends(get_current_user),
    asset_service: PortfolioAssetService = Depends(get_portfolio_asset_service)
) -> PortfolioAssetDetailResponse:
    """Получение детальной информации об активе"""
    return await asset_service.get_asset_detail(asset_id, current_user.id)
