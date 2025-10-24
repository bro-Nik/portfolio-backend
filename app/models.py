from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from sqlalchemy.sql import func
from sqlalchemy import String
from sqlalchemy.orm import Mapped, backref
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from .database import Base


class Portfolio(Base):
    __tablename__ = "portfolio"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    name: Mapped[str] = mapped_column(String(100))
    market: Mapped[str] = mapped_column(String(32))
    comment: Mapped[Optional[str]] = mapped_column(String(1024))

    # Relationships
    assets: Mapped[List["Asset"]] = relationship(back_populates="portfolio", lazy="select")
    transactions: Mapped[List["Transaction"]] = relationship(back_populates="portfolio", lazy="select")



class Asset(Base):
    __tablename__ = "asset"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    ticker_id: Mapped[str] = mapped_column(String(256))
    portfolio_id: Mapped[int] = mapped_column(Integer, ForeignKey("portfolio.id"))
    quantity: Mapped[float] = mapped_column(Float, default=0.0)
    buy_orders: Mapped[float] = mapped_column(Float, default=0.0)
    sell_orders: Mapped[float] = mapped_column(Float, default=0.0)
    amount: Mapped[float] = mapped_column(Float, default=0.0)
    percent: Mapped[float] = mapped_column(Float, default=0.0)
    comment: Mapped[Optional[str]] = mapped_column(String(1024))

    # Relationships
    portfolio: Mapped["Portfolio"] = relationship(back_populates="assets")
    transactions: Mapped[List['Transaction']] = relationship(
        "Transaction",
        primaryjoin="and_(or_(Asset.ticker_id == foreign(Transaction.ticker_id), Asset.ticker_id == foreign(Transaction.ticker2_id)), "
                    "Asset.portfolio_id == Transaction.portfolio_id)",
        backref=backref('portfolio_asset')
    )


class Transaction(Base):
    __tablename__ = "transaction"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc))
    ticker_id: Mapped[str] = mapped_column(String(32))
    ticker2_id: Mapped[Optional[str]] = mapped_column(String(32))
    quantity: Mapped[float] = mapped_column(Float)
    quantity2: Mapped[Optional[float]] = mapped_column(Float)
    price: Mapped[Optional[float]] = mapped_column(Float)
    price_usd: Mapped[Optional[float]] = mapped_column(Float)
    type: Mapped[str] = mapped_column(String(24))
    comment: Mapped[Optional[str]] = mapped_column(String(1024))
    wallet_id: Mapped[int] = mapped_column(Integer)
    portfolio_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("portfolio.id"))
    order: Mapped[bool] = mapped_column(default=False)
    related_transaction_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("transaction.id"))

    # Relationships
    portfolio: Mapped[Optional["Portfolio"]] = relationship(back_populates="transactions")
    related_transaction: Mapped[Optional["Transaction"]] = relationship(
        foreign_keys=[related_transaction_id],
        remote_side=[id],
        uselist=False
    )
