from datetime import datetime, timezone
from typing import List, Optional
from decimal import Decimal

from sqlalchemy import Integer, String, ForeignKey, DateTime, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship, backref

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
    quantity: Mapped[Decimal] = mapped_column(Numeric, default=0.0)
    buy_orders: Mapped[Decimal] = mapped_column(Numeric, default=0.0)
    sell_orders: Mapped[Decimal] = mapped_column(Numeric, default=0.0)
    amount: Mapped[Decimal] = mapped_column(Numeric, default=0.0)
    percent: Mapped[Decimal] = mapped_column(Numeric, default=0.0)
    comment: Mapped[Optional[str]] = mapped_column(String(1024))

    # Relationships
    portfolio: Mapped["Portfolio"] = relationship(back_populates="assets")
    transactions: Mapped[List['Transaction']] = relationship(
        "Transaction",
        primaryjoin="and_(or_(Asset.ticker_id == foreign(Transaction.ticker_id), Asset.ticker_id == foreign(Transaction.ticker2_id)), "
                    "or_(Asset.portfolio_id == Transaction.portfolio_id, Asset.portfolio_id == Transaction.portfolio2_id))",
        backref=backref('portfolio_asset')
    )


class Transaction(Base):
    __tablename__ = "transaction"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc))
    ticker_id: Mapped[str] = mapped_column(String(32))
    ticker2_id: Mapped[Optional[str]] = mapped_column(String(32))
    quantity: Mapped[Decimal] = mapped_column(Numeric)
    quantity2: Mapped[Optional[Decimal]] = mapped_column(Numeric)
    price: Mapped[Optional[Decimal]] = mapped_column(Numeric)
    price_usd: Mapped[Optional[Decimal]] = mapped_column(Numeric)
    type: Mapped[str] = mapped_column(String(24))
    comment: Mapped[Optional[str]] = mapped_column(String(1024))
    wallet_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("wallet.id"))
    wallet2_id: Mapped[Optional[int]] = mapped_column(Integer)
    portfolio_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("portfolio.id"))
    portfolio2_id: Mapped[Optional[int]] = mapped_column(Integer)
    order: Mapped[bool] = mapped_column(default=False)
    related_transaction_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("transaction.id"))

    # Relationships
    portfolio: Mapped[Optional["Portfolio"]] = relationship(back_populates="transactions")
    wallet: Mapped[Optional["Wallet"]] = relationship(back_populates='transactions')
    related_transaction: Mapped[Optional["Transaction"]] = relationship(
        foreign_keys=[related_transaction_id],
        remote_side=[id],
        uselist=False
    )

    def get_direction(self, cancel: bool = False) -> int:
        """Метод для расчета направления"""
        positive_types = {'Buy', 'Input', 'TransferIn', 'Earning'}
        direction = 1 if self.type in positive_types else -1
        return direction * -1 if cancel else direction


class Wallet(Base):
    __tablename__ = "wallet"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    name: Mapped[str] = mapped_column(String(255))
    comment: Mapped[str | None] = mapped_column(String(1024))

    # Relationships
    assets: Mapped[List["WalletAsset"]] = relationship(back_populates="wallet", lazy="select")
    transactions: Mapped[List['Transaction']] = relationship(back_populates='wallet',
                                          order_by='Transaction.date.desc()')


class WalletAsset(Base):
    __tablename__ = "wallet_asset"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticker_id: Mapped[str] = mapped_column(String(256))
    wallet_id: Mapped[int] = mapped_column(ForeignKey("wallet.id"))
    quantity: Mapped[Decimal] = mapped_column(Numeric, default=0.0)
    buy_orders: Mapped[Decimal] = mapped_column(Numeric, default=0.0)
    sell_orders: Mapped[Decimal] = mapped_column(Numeric, default=0.0)

    # Relationships
    wallet: Mapped["Wallet"] = relationship(back_populates="assets")
    transactions: Mapped[List['Transaction']] = relationship(
        "Transaction",
        primaryjoin="and_(or_(WalletAsset.ticker_id == foreign(Transaction.ticker_id),"
                    "WalletAsset.ticker_id == foreign(Transaction.ticker2_id)),"
                    "WalletAsset.wallet_id == foreign(Transaction.wallet_id))",
        viewonly=True,
        backref=backref('wallet_asset', lazy=True)
    )
