from typing import List
from app.schemas.portfolio import PortfolioCreateRequest, PortfolioUpdateRequest
from app.schemas.portfolio_asset import PortfolioAssetCreateRequest
from fastapi import APIRouter, Depends, HTTPException, Query
from app.services.portfolio_asset import PortfolioAssetService

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
async def get_user_portfolios(
    current_user: User = Depends(get_current_user),
    portfolio_service: PortfolioService = Depends(get_portfolio_service)
) -> PortfolioListResponse:
    """Получение всех портфелей пользователя"""
    try:
        portfolios = await portfolio_service.get_portfolios(current_user.id)
        return PortfolioListResponse(portfolios=portfolios)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=PortfolioListResponse)
async def get_user_portfolios_by_ids(
    ids: List[int] = Query(..., description="Список ID портфелей"),
    current_user: User = Depends(get_current_user),
    portfolio_service: PortfolioService = Depends(get_portfolio_service)
) -> PortfolioListResponse:
    """Получение портфелей пользователя по списку id"""
    try:
        portfolios = await portfolio_service.get_portfolios(current_user.id, ids)
        return PortfolioListResponse(portfolios=portfolios)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=PortfolioResponse)
async def create_portfolio(
    portfolio_data: PortfolioCreateRequest,
    current_user: User = Depends(get_current_user),
    portfolio_service: PortfolioService = Depends(get_portfolio_service)
) -> PortfolioResponse:
    """Создание нового портфеля"""
    try:
        portfolio = await portfolio_service.create_portfolio(current_user.id, portfolio_data)
        return portfolio
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{portfolio_id}", response_model=PortfolioResponse)
async def update_portfolio(
    portfolio_id: int,
    portfolio_data: PortfolioUpdateRequest,
    current_user: User = Depends(get_current_user),
    portfolio_service: PortfolioService = Depends(get_portfolio_service)
) -> PortfolioResponse:
    """Обновление портфеля"""
    try:
        portfolio = await portfolio_service.update_portfolio(
            portfolio_id, current_user.id, portfolio_data
        )
        return portfolio
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{portfolio_id}", response_model=PortfolioDeleteResponse)
async def delete_portfolio(
    portfolio_id: int,
    current_user: User = Depends(get_current_user),
    portfolio_service: PortfolioService = Depends(get_portfolio_service)
) -> PortfolioDeleteResponse:
    """Удаление портфеля"""
    try:
        await portfolio_service.delete_portfolio(portfolio_id, current_user.id)
        return PortfolioDeleteResponse(portfolio_id=portfolio_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{portfolio_id}/assets", response_model=PortfolioResponse)
async def add_asset_to_portfolio(
    portfolio_id: int,
    data: PortfolioAssetCreateRequest,
    current_user: User = Depends(get_current_user),
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
    asset_service: PortfolioAssetService = Depends(get_portfolio_asset_service)
) -> PortfolioResponse:
    """Добавление актива в портфель"""
    try:
        data.portfolio_id=portfolio_id
        await asset_service.create_asset(data)

        return await portfolio_service.get_portfolio(portfolio_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{portfolio_id}/assets/{asset_id}", response_model=PortfolioResponse)
async def delete_asset_from_portfolio(
    portfolio_id: int,
    asset_id: int,
    current_user: User = Depends(get_current_user),
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
    asset_service: PortfolioAssetService = Depends(get_portfolio_asset_service)
) -> PortfolioResponse:
    """Удаление актива из портфеля"""
    try:
        await asset_service.delete_asset(asset_id)
        return await portfolio_service.get_portfolio(portfolio_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assets/{asset_id}", response_model=PortfolioAssetDetailResponse)
async def get_asset(
    asset_id: int,
    current_user: User = Depends(get_current_user),
    asset_service: PortfolioAssetService = Depends(get_portfolio_asset_service)
) -> PortfolioAssetDetailResponse:
    """Получение детальной информации об активе"""
    try:
        return await asset_service.get_asset_detail(asset_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
