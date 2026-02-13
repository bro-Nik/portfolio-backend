from fastapi import APIRouter

from app.api.user.endpoints import portfolios, transactions, wallets

user_router = APIRouter()

user_router.include_router(portfolios.router)
user_router.include_router(wallets.router)
user_router.include_router(transactions.router)
