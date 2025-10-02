from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import models, database


router = APIRouter(prefix="/api/portfolios", tags=["portfolios"])


@router.get("/user/{user_id}")
def get_user_portfolios(user_id: int, db: Session = Depends(database.get_db)):
    portfolios = db.query(models.Portfolio).filter(models.Portfolio.user_id == user_id).all()

    for portfolio in portfolios:

        portfolio.cost_now = 0
        portfolio.amount = 0
        portfolio.buy_orders = 0
        portfolio.invested = 0

        for asset in portfolio.assets:
            asset.cost_now = asset.quantity * asset.ticker.price
            portfolio.cost_now += asset.cost_now
            portfolio.amount += asset.amount
            portfolio.buy_orders += asset.buy_orders

    return {
        "portfolios": portfolios
    }
