from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.dependencies.auth import get_current_user, User
from app.dependencies.transaction import get_transaction_service
from app.services.transaction import TransactionService
from app.schemas import TransactionCreate


class ActionResponse(BaseModel):
    success: bool
    message: Optional[str] = None


router = APIRouter(prefix="/api/transactions", tags=["transactions"])


@router.post("/transaction", response_model=ActionResponse)
async def create_transaction(
    transaction_data: TransactionCreate,
    current_user: User = Depends(get_current_user),
    transaction_service: TransactionService = Depends(get_transaction_service),
) -> ActionResponse:
    """Создание новой транзакции"""
    try:
        await transaction_service.create(current_user.id, transaction_data)
        return ActionResponse(success=True, message="Транзакция успешно создана")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/transaction/{transaction_id}", response_model=ActionResponse)
async def update_transaction(
    transaction_id: int,
    transaction_data: TransactionCreate,
    current_user: User = Depends(get_current_user),
    transaction_service: TransactionService = Depends(get_transaction_service),
) -> ActionResponse:
    """Создание новой транзакции"""
    try:
        await transaction_service.update(current_user.id, transaction_id, transaction_data)
        return ActionResponse(success=True, message="Транзакция успешно изменена")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/transaction/{transaction_id}", response_model=ActionResponse)
async def delete_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    transaction_service: TransactionService = Depends(get_transaction_service),
) -> ActionResponse:
    """Создание новой транзакции"""
    try:
        await transaction_service.delete(current_user.id, transaction_id)
        return ActionResponse(success=True, message="Транзакция успешно удалена")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
