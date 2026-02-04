from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.dependencies.auth import get_current_user, User
from app.dependencies.transaction import get_transaction_service
from app.services.transaction import TransactionService
from app.schemas import TransactionCreateRequest, TransactionResponseWithAssets, PortfolioAssetResponse, WalletAssetResponse


router = APIRouter(prefix="/api/transactions", tags=["transactions"])


@router.post("/", response_model=TransactionResponseWithAssets)
async def create_transaction(
    transaction_data: TransactionCreateRequest,
    user: User = Depends(get_current_user),
    transaction_service: TransactionService = Depends(get_transaction_service),
) -> TransactionResponseWithAssets:
    """Создание новой транзакции"""
    try:
        # Создаем транзакцию
        print(transaction_data)
        transaction = await transaction_service.create_transaction(user.id, transaction_data)

        # Получаем измененные активы на основе созданной транзакции
        portfolio_assets = await transaction_service.get_affected_portfolio_assets([transaction])
        wallet_assets = await transaction_service.get_affected_wallet_assets([transaction])
        return TransactionResponseWithAssets(
            message="Транзакция успешно создана",
            portfolio_assets=portfolio_assets,
            wallet_assets=wallet_assets,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{transaction_id}", response_model=TransactionResponseWithAssets)
async def update_transaction(
    transaction_id: int,
    transaction_data: TransactionCreateRequest,
    user: User = Depends(get_current_user),
    transaction_service: TransactionService = Depends(get_transaction_service),
) -> TransactionResponseWithAssets:
    """Изменение транзакции"""
    try:
        new_transaction, old_transaction = await transaction_service.update_transaction(
            user.id, transaction_id, transaction_data
        )
        transactions = [new_transaction, old_transaction]

        # Получаем измененные активы на основе измененной транзакции
        portfolio_assets = await transaction_service.get_affected_portfolio_assets(transactions)
        wallet_assets = await transaction_service.get_affected_wallet_assets(transactions)
        return TransactionResponseWithAssets(
            message="Транзакция успешно изменена",
            portfolio_assets=[PortfolioAssetResponse.model_validate(a) for a in portfolio_assets],
            wallet_assets=[WalletAssetResponse.model_validate(a) for a in wallet_assets],
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{transaction_id}", response_model=TransactionResponseWithAssets)
async def delete_transaction(
    transaction_id: int,
    user: User = Depends(get_current_user),
    transaction_service: TransactionService = Depends(get_transaction_service),
) -> TransactionResponseWithAssets:
    """Удаление транзакции"""
    try:
        transaction = await transaction_service.delete_transaction(user.id, transaction_id)
        # Получаем измененные активы на основе созданной транзакции
        portfolio_assets = await transaction_service.get_affected_portfolio_assets([transaction])
        wallet_assets = await transaction_service.get_affected_wallet_assets([transaction])
        return TransactionResponseWithAssets(
            message="Транзакция успешно удалена",
            portfolio_assets=[PortfolioAssetResponse.model_validate(a) for a in portfolio_assets],
            wallet_assets=[WalletAssetResponse.model_validate(a) for a in wallet_assets],
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
