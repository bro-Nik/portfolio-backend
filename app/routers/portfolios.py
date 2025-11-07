from fastapi import APIRouter, Depends, HTTPException

from app.dependencies.auth import get_current_user, User
from app.dependencies.portfolio import get_portfolio_service
from app.services.portfolio import PortfolioService
from app.schemas import (
    PortfolioResponse,
    PortfolioListResponse,
    PortfolioEdit,
    PortfolioDeleteResponse,
    AssetDetailResponse,
    TickerData
)


router = APIRouter(prefix="/api/portfolios", tags=["portfolios"])


@router.get("/", response_model=PortfolioListResponse)
async def get_user_portfolios(
    current_user: User = Depends(get_current_user),
    portfolio_service: PortfolioService = Depends(get_portfolio_service)
) -> PortfolioListResponse:
    """Получение всех портфелей пользователя"""
    # try:
    portfolios = await portfolio_service.get_user_portfolios(current_user.id)
    return PortfolioListResponse(portfolios=portfolios)
    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=PortfolioResponse)
async def create_portfolio(
    portfolio_data: PortfolioEdit,
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
    portfolio_data: PortfolioEdit,
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
    data: TickerData,
    current_user: User = Depends(get_current_user),
    portfolio_service: PortfolioService = Depends(get_portfolio_service)
) -> PortfolioResponse:
    """Добавление актива в портфель"""
    try:
        portfolio = await portfolio_service.add_asset(
            portfolio_id, current_user.id, data.ticker_id
        )
        return portfolio
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{portfolio_id}/assets/{asset_id}", response_model=PortfolioResponse)
async def delete_asset_from_portfolio(
    portfolio_id: int,
    asset_id: int,
    current_user: User = Depends(get_current_user),
    portfolio_service: PortfolioService = Depends(get_portfolio_service)
) -> PortfolioResponse:
    """Удаление актива из портфеля"""
    try:
        portfolio = await portfolio_service.remove_asset(
            portfolio_id, current_user.id, asset_id
        )
        return portfolio
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assets/{asset_id}", response_model=AssetDetailResponse)
async def get_asset(
    asset_id: int,
    current_user: User = Depends(get_current_user),
    portfolio_service: PortfolioService = Depends(get_portfolio_service)
) -> AssetDetailResponse:
    """Получение детальной информации об активе"""
    try:
        asset_detail = await portfolio_service.get_asset_detail(asset_id, current_user.id)
        return AssetDetailResponse(**asset_detail)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
