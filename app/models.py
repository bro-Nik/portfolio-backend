from typing import List
from datetime import datetime, date, timezone

from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from sqlalchemy.sql import func
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy.orm import Mapped, backref
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from .database import Base


class Portfolio(Base):
    __tablename__ = "portfolio"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    name = Column(String(100))
    market: Mapped[str] = mapped_column(String(32))

    # Relationships
    assets: Mapped[List['Asset']] = relationship(back_populates="portfolio", lazy=True)
    transactions: Mapped[List['Transaction']] = relationship(back_populates="portfolio", lazy=True)


class Asset(Base):
    __tablename__ = "asset"

    id = Column(Integer, primary_key=True, index=True)
    ticker_id: Mapped[str] = mapped_column(String(256), ForeignKey("ticker.id"))
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolio.id"))
    quantity: Mapped[float] = mapped_column(default=0)
    buy_orders: Mapped[float] = mapped_column(default=0)
    sell_orders: Mapped[float] = mapped_column(default=0)
    amount: Mapped[float] = mapped_column(default=0)
    percent: Mapped[float] = mapped_column(default=0)
    comment: Mapped[str | None] = mapped_column(String(1024))

    # Relationships
    portfolio: Mapped['Portfolio'] = relationship(back_populates='assets', lazy=True)
    ticker: Mapped['Ticker'] = relationship(foreign_keys=ticker_id, back_populates="assets", lazy=True)
    transactions: Mapped[List['Transaction']] = relationship(
        "Transaction",
        primaryjoin="and_(or_(Asset.ticker_id == foreign(Transaction.ticker_id), Asset.ticker_id == foreign(Transaction.ticker2_id)), "
                    "Asset.portfolio_id == Transaction.portfolio_id)",
        backref=backref('portfolio_asset', lazy=True)
    )


class Transaction(Base):
    __tablename__ = "transaction"

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[datetime] = mapped_column(default=datetime.now(timezone.utc))
    ticker_id: Mapped[str] = mapped_column(String(32), ForeignKey("ticker.id"))
    ticker2_id: Mapped[str | None] = mapped_column(String(32), ForeignKey("ticker.id"))
    quantity: Mapped[float] = mapped_column()
    quantity2: Mapped[float | None] = mapped_column()
    price: Mapped[float | None] = mapped_column()
    price_usd: Mapped[float | None] = mapped_column()
    type: Mapped[str] = mapped_column(String(24))
    comment: Mapped[str | None] = mapped_column(String(1024))
    # wallet_id: Mapped[int] = mapped_column(ForeignKey("wallet.id"))
    portfolio_id: Mapped[int | None] = mapped_column(ForeignKey("portfolio.id"))
    order: Mapped[bool] = mapped_column(default=False)
    related_transaction_id: Mapped[int | None] = mapped_column(ForeignKey("transaction.id"))

    # Relationships
    # alert: Mapped['Alert'] = relationship(back_populates='transaction', lazy=True)
    portfolio: Mapped['Portfolio'] = relationship(back_populates='transactions', lazy=True)
    # wallet: Mapped['Wallet'] = relationship(back_populates='transactions', lazy=True)
    base_ticker: Mapped['Ticker'] = relationship(foreign_keys=[ticker_id], viewonly=True)
    quote_ticker: Mapped['Ticker'] = relationship(foreign_keys=[ticker2_id], viewonly=True)
    related_transaction: Mapped['Transaction'] = relationship(foreign_keys=[related_transaction_id], uselist=False)


class Ticker(Base):
    __tablename__ = "ticker"

    id: Mapped[str] = mapped_column(String(256), primary_key=True)
    name: Mapped[str] = mapped_column(String(1024))
    symbol: Mapped[str] = mapped_column(String(124))
    image: Mapped[str | None] = mapped_column(String(1024))
    market_cap_rank: Mapped[int | None] = mapped_column()
    price: Mapped[float] = mapped_column(default=0)
    market: Mapped[str] = mapped_column(String(32))

    # Relationships
    assets: Mapped[List['Asset']] = relationship()
