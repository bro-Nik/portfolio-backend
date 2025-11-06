from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, validator

from app import models, database
from app.dependencies.auth import get_current_user, User
from app.schemas.portfolio import AssetResponse, PortfolioResponse, \
        PortfolioListResponse, PortfolioEdit, PortfolioDeleteResponse, TickerData


router = APIRouter(prefix="/api/portfolios", tags=["portfolios"])


def _prepare_asset_response(asset: models.Asset) -> AssetResponse:
    """Подготовка данных актива для ответа"""
    return AssetResponse(
        id=asset.id,
        ticker_id=asset.ticker_id,
        quantity=asset.quantity,
        amount=asset.amount,
        buy_orders=asset.buy_orders,
    )


def _prepare_portfolio_response(
    portfolio: models.Portfolio,
    include_assets: bool = False
) -> PortfolioResponse:
    """Подготовка данных портфеля для ответа"""
    portfolio_data = {
        'id': portfolio.id,
        'name': portfolio.name,
        'market': portfolio.market,
        'comment': portfolio.comment,
        'assets': []
    }

    if include_assets and portfolio.assets:
        portfolio_data['assets'] = [
            _prepare_asset_response(asset) for asset in portfolio.assets
        ]

    return PortfolioResponse(**portfolio_data)


async def _get_user_portfolio(
    portfolio_id: int,
    user_id: int,
    db: AsyncSession,
    load_assets: bool = False
) -> models.Portfolio:
    """Получение портфеля с проверкой прав доступа"""
    query = select(models.Portfolio).where(
        models.Portfolio.id == portfolio_id,
        models.Portfolio.user_id == user_id
    )

    if load_assets:
        query = query.options(selectinload(models.Portfolio.assets))

    result = await db.execute(query)
    portfolio = result.scalar_one_or_none()

    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Портфель не найден"
        )

    return portfolio


@router.get("/", response_model=PortfolioListResponse)
async def get_user_portfolios(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(database.get_db)
) -> PortfolioListResponse:
    """Получение всех портфелей пользователя"""
    result = await db.execute(
        select(models.Portfolio)
        .where(models.Portfolio.user_id == current_user.id)
        .options(
            selectinload(models.Portfolio.assets)
        )
    )
    portfolios = result.scalars().all()

    portfolios_data = [
        _prepare_portfolio_response(portfolio, include_assets=True)
        for portfolio in portfolios
    ]

    return PortfolioListResponse(portfolios=portfolios_data)


@router.post("/", response_model=PortfolioResponse)
async def create_portfolio(
    portfolio_data: PortfolioEdit,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(database.get_db)
) -> PortfolioResponse:
    """Создание нового портфеля"""

    portfolio = models.Portfolio(
        user_id=current_user.id,
        name=portfolio_data.name,
        market=portfolio_data.market,
        comment=portfolio_data.comment
    )

    db.add(portfolio)
    await db.commit()
    await db.refresh(portfolio)

    return _prepare_portfolio_response(portfolio)


@router.put("/{portfolio_id}", response_model=PortfolioResponse)
async def update_portfolio(
    portfolio_id: int,
    portfolio_data: PortfolioEdit,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(database.get_db)
) -> PortfolioResponse:
    """Обновление портфеля"""

    portfolio = await _get_user_portfolio(portfolio_id, current_user.id, db)

    # Обновляем поля
    portfolio.name = portfolio_data.name
    portfolio.market = portfolio_data.market
    portfolio.comment = portfolio_data.comment

    await db.commit()
    await db.refresh(portfolio)

    return _prepare_portfolio_response(portfolio)


@router.delete("/{portfolio_id}", response_model=PortfolioDeleteResponse)
async def delete_portfolio(
    portfolio_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(database.get_db)
) -> PortfolioDeleteResponse:
    """Удаление портфеля пользователя"""
    portfolio = await _get_user_portfolio(portfolio_id, current_user.id, db)

    await db.delete(portfolio)
    await db.commit()

    return PortfolioDeleteResponse(portfolio_id=portfolio_id)


@router.post("/{portfolio_id}/assets", response_model=PortfolioResponse)
async def add_asset_to_portfolio(
    portfolio_id: int,
    data: TickerData,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(database.get_db)
) -> PortfolioResponse:
    """Добавление актива в портфель"""
    ticker_id = data.ticker_id

    # Проверка прав на портфель
    await _get_user_portfolio(portfolio_id, current_user.id, db)

    # Валидация входных данных
    if not ticker_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID актива обязателен"
        )

    # ToDo Проверить существование тикера
    # if not ticker:
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND,
    #         detail="Актив не найден"
    #     )

    # Проверяем, не добавлен ли уже этот актив в портфель
    result = await db.execute(
        select(models.Asset).where(
            models.Asset.portfolio_id == portfolio_id,
            models.Asset.ticker_id == ticker_id
        )
    )
    existing_asset = result.scalar_one_or_none()

    if existing_asset:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Этот актив уже добавлен в портфель"
        )

    # Создаем новый актив
    new_asset = models.Asset(
        portfolio_id=portfolio_id,
        ticker_id=ticker_id
    )

    db.add(new_asset)
    await db.commit()
    await db.refresh(new_asset)

    # Возвращаем обновленный портфель
    updated_portfolio = await _get_user_portfolio(portfolio_id, current_user.id, db, True)
    return _prepare_portfolio_response(updated_portfolio, include_assets=True)


@router.delete("/{portfolio_id}/assets/{asset_id}", response_model=PortfolioResponse)
async def delete_asset_from_portfolio(
    portfolio_id: int,
    asset_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(database.get_db)
) -> PortfolioResponse:
    """Удаление актива из портфеля"""

    # Проверка прав на портфель
    await _get_user_portfolio(portfolio_id, current_user.id, db)

    # Находим актив в портфеле
    result = await db.execute(
        select(models.Asset).where(
            models.Asset.id == asset_id,
            models.Asset.portfolio_id == portfolio_id
        )
    )
    asset = result.scalar_one_or_none()

    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Актив не найден в портфеле"
        )

    # Удаляем актив
    await db.delete(asset)
    await db.commit()

    # Возвращаем обновленный портфель
    updated_portfolio = await _get_user_portfolio(portfolio_id, current_user.id, db, True)
    return _prepare_portfolio_response(updated_portfolio, include_assets=True)


@router.get("/assets/{asset_id}")
async def get_asset(
    asset_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(database.get_db)
):
    """
    Получить детальную информацию об активе включая историю, аналитику и т.д.
    """
    # Загружаем актив с тикером и портфелем
    result = await db.execute(
        select(models.Asset)
        .join(models.Portfolio)
        .where(
            models.Asset.id == asset_id,
            models.Portfolio.user_id == int(current_user.id)
        )
        .options(
            selectinload(models.Asset.portfolio),
            selectinload(models.Asset.transactions)
        )
    )
    asset = result.scalar_one_or_none()

    if not asset:
        raise HTTPException(status_code=404, detail="Актив не найден")

    asset_transactions = []
    for transaction in asset.transactions:
        asset_transactions.append({
            "id": transaction.id,
            "portfolio_id": transaction.portfolio_id,
            "wallet_id": transaction.wallet_id,
            "date": transaction.date,
            "ticker_id": transaction.ticker_id,
            "ticker2_id": transaction.ticker2_id,
            "quantity": transaction.quantity,
            "quantity2": transaction.quantity2,
            "price": transaction.price,
            "type": transaction.type,
            "comment": transaction.comment,
        })

    # Рассчитываем распределение по портфелям (если актив есть в нескольких портфелях)
    result_all = await db.execute(
        select(models.Asset)
        .join(models.Asset.portfolio)
        .where(
            models.Asset.ticker_id == asset.ticker_id,
            models.Portfolio.user_id == current_user.id
        )
        .options(selectinload(models.Asset.portfolio))
    )
    all_assets_same_ticker = result_all.scalars().all()

    portfolio_distribution = []
    total_quantity_all_portfolios = 0
    total_amount_all_portfolios = 0

    for asset_item in all_assets_same_ticker:
        total_quantity_all_portfolios += asset_item.quantity
        total_amount_all_portfolios += asset_item.amount
        portfolio_distribution.append({
            "portfolio_id": asset_item.portfolio.id,
            "portfolio_name": asset_item.portfolio.name,
            "quantity": asset_item.quantity,
            "amount": asset_item.amount,
            "percentage_of_total": (asset_item.quantity / total_quantity_all_portfolios * 100) if total_quantity_all_portfolios > 0 else 0
        })

    # Формируем ответ
    asset_detail = {
        "transactions": asset_transactions,
        "distribution": {
            "total_quantity_all_portfolios": total_quantity_all_portfolios,
            "total_amount_all_portfolios": total_amount_all_portfolios,
            "portfolios": portfolio_distribution
        },
    }

    return asset_detail
