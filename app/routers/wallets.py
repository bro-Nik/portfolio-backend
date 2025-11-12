from typing import List, Union
from pydantic import BaseModel
from app import database
from app.schemas.wallet import ErrorResponse, WalletToBuyResponse, WalletToSellResponse
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import get_current_user, User
from app.dependencies.wallet import get_wallet_service
from app.services.wallet import WalletService
from app.schemas import (
    WalletListResponse,
    WalletResponse,
    WalletEdit,
    WalletDeleteResponse
)


router = APIRouter(prefix="/api/wallets", tags=["wallets"])


@router.get("/", response_model=WalletListResponse)
async def get_user_wallets(
    current_user: User = Depends(get_current_user),
    wallet_service: WalletService = Depends(get_wallet_service)
) -> WalletListResponse:
    """Получение всех кошельков пользователя"""
    try:
        wallets = await wallet_service.get_user_wallets(current_user.id)
        return WalletListResponse(wallets=wallets)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=WalletResponse)
async def create_wallet(
    wallet_data: WalletEdit,
    current_user: User = Depends(get_current_user),
    wallet_service: WalletService = Depends(get_wallet_service)
) -> WalletResponse:
    """Создание нового кошелька"""
    try:
        wallet = await wallet_service.create_wallet(current_user.id, wallet_data)
        return wallet
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{wallet_id}", response_model=WalletResponse)
async def update_wallet(
    wallet_id: int,
    wallet_data: WalletEdit,
    current_user: User = Depends(get_current_user),
    wallet_service: WalletService = Depends(get_wallet_service)
) -> WalletResponse:
    """Обновление кошелька"""
    try:
        wallet = await wallet_service.update_wallet(
            wallet_id, current_user.id, wallet_data
        )
        return wallet
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{wallet_id}", response_model=WalletDeleteResponse)
async def delete_wallet(
    wallet_id: int,
    current_user: User = Depends(get_current_user),
    wallet_service: WalletService = Depends(get_wallet_service)
) -> WalletDeleteResponse:
    """Удаление кошелька"""
    try:
        await wallet_service.delete_wallet(wallet_id, current_user.id)
        return WalletDeleteResponse(wallet_id=wallet_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/wallets_to_sell',
           response_model=Union[List[WalletToSellResponse], ErrorResponse],
           summary="Получить кошельки для продажи",
           description="Возвращает список кошельков с доступными активами для продажи")
async def wallets_to_sell(
    ticker_id: str = Query(..., description="ID тикера"),
    current_user: User = Depends(get_current_user),
    wallet_service: WalletService = Depends(get_wallet_service)
):
    result = []
    wallets = await wallet_service.get_user_wallets(current_user.id)

    for wallet in wallets:
        for asset in wallet.assets:
            if ticker_id != asset.ticker_id:
                continue

            asset_free = asset.quantity - asset.sell_orders
            if asset_free > 0:
                quantity = asset_free
                result.append(WalletToSellResponse(
                    id=wallet.id,
                    name=wallet.name,
                    sort=asset_free,
                    free=asset_free,
                    subtext=f'({quantity})'
                ))

    if result:
        # Сортировка по убыванию
        result.sort(key=lambda wallet: wallet.sort, reverse=True)
        return result

    # return ErrorResponse(message="В кошельках нет свободных остатков")


@router.get('/wallets_to_buy',
           response_model=List[WalletToBuyResponse],
           summary="Получить кошельки для покупки",
           description="Возвращает список кошельков с их текущей стоимостью")
async def wallets_to_buy(
    current_user: User = Depends(get_current_user),
    wallet_service: WalletService = Depends(get_wallet_service)
):
    result = []
    wallets = await wallet_service.get_user_wallets(current_user.id)

    for wallet in wallets:
        result.append(WalletToBuyResponse(
            id=wallet.id,
            name=wallet.name
        ))

    return result


class AssetToTransactionResponse(BaseModel):
    ticker_id: str
    free: float


@router.get('/{wallet_id}/assets',
           response_model=List[AssetToTransactionResponse],
           summary="Получить активы кошелька",
           description="Возвращает список активов в кошельке и доступные тикеры")
async def wallet_assets(
    wallet_id: int,
    current_user: User = Depends(get_current_user),
    wallet_service: WalletService = Depends(get_wallet_service),
):
    result = []
    in_wallet = []

    # Получаем кошелек
    wallet = await wallet_service.get_user_wallet(wallet_id, current_user.id)

    # Обновляем цены и получаем активы
    assets = wallet.assets

    # Добавляем активы из кошелька
    for asset in assets:
        asset_free = asset.quantity - asset.sell_orders
        if asset_free:
            result.append(AssetToTransactionResponse(
                ticker_id=asset.ticker_id,
                free=asset.quantity
            ))
            in_wallet.append(asset.ticker_id)

    return result

# @bp.route('/wallets_to_transfer_out', methods=['GET'])
# @login_required
# def wallets_to_transfer_out():
#     wallet_id = request.args['wallet_id']
#     ticker_id = request.args['ticker_id']
#     result = []
#
#     if len(current_user.wallets) == 1:
#         return json.dumps({'message': gettext('У вас только один кошелек')})
#
#     for wallet in current_user.wallets:
#         if int(wallet_id) == wallet.id:
#             continue
#
#         quantity = sort = 0
#         for asset in wallet.assets:
#             if ticker_id != asset.ticker_id:
#                 continue
#
#             quantity = currency_price(asset.free, asset.ticker.symbol)
#             sort = asset.free
#         info = {'value': str(wallet.id), 'text': wallet.name, 'sort': sort}
#         if sort > 0:
#             info['subtext'] = f"({quantity})"
#         result.append(info)
#
#     if result:
#         result = sorted(result,
#                         key=lambda wallet_: wallet_.get('sort'), reverse=True)
#
#     return json.dumps(result)
#
#
