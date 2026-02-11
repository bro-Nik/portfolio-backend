from datetime import UTC, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, backref, declarative_base, mapped_column, relationship

Base = declarative_base()


class Portfolio(Base):
    __tablename__ = 'portfolio'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    name: Mapped[str] = mapped_column(String(100))
    market: Mapped[str] = mapped_column(String(32))
    comment: Mapped[str | None] = mapped_column(String(1024))

    # Relationships
    assets: Mapped[list['Asset']] = relationship(back_populates='portfolio', lazy='select')
    transactions: Mapped[list['Transaction']] = relationship(back_populates='portfolio', lazy='select')



class Asset(Base):
    __tablename__ = 'asset'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    ticker_id: Mapped[str] = mapped_column(String(256))
    portfolio_id: Mapped[int] = mapped_column(Integer, ForeignKey('portfolio.id'))
    quantity: Mapped[Decimal] = mapped_column(Numeric, default=Decimal(0))
    buy_orders: Mapped[Decimal] = mapped_column(Numeric, default=Decimal(0))
    sell_orders: Mapped[Decimal] = mapped_column(Numeric, default=Decimal(0))
    amount: Mapped[Decimal] = mapped_column(Numeric, default=Decimal(0))
    percent: Mapped[Decimal] = mapped_column(Numeric, default=Decimal(0))
    comment: Mapped[str | None] = mapped_column(String(1024))

    # Relationships
    portfolio: Mapped['Portfolio'] = relationship(back_populates='assets')


class Transaction(Base):
    __tablename__ = 'transaction'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(UTC))
    ticker_id: Mapped[str] = mapped_column(String(32))
    ticker2_id: Mapped[str | None] = mapped_column(String(32))
    quantity: Mapped[Decimal] = mapped_column(Numeric)
    quantity2: Mapped[Decimal | None] = mapped_column(Numeric)
    price: Mapped[Decimal | None] = mapped_column(Numeric)
    price_usd: Mapped[Decimal | None] = mapped_column(Numeric)
    type: Mapped[str] = mapped_column(String(24))
    comment: Mapped[str | None] = mapped_column(String(1024))
    wallet_id: Mapped[int | None] = mapped_column(Integer, ForeignKey('wallet.id'))
    wallet2_id: Mapped[int | None] = mapped_column(Integer)
    portfolio_id: Mapped[int | None] = mapped_column(Integer, ForeignKey('portfolio.id'))
    portfolio2_id: Mapped[int | None] = mapped_column(Integer)
    order: Mapped[bool | None] = mapped_column(Boolean)

    # Relationships
    portfolio: Mapped[Optional['Portfolio']] = relationship(back_populates='transactions')
    wallet: Mapped[Optional['Wallet']] = relationship(back_populates='transactions')

    def get_direction(self, cancel: bool = False) -> int:
        """Метод для расчета направления."""
        positive_types = {'Buy', 'Input', 'TransferIn', 'Earning'}
        direction = 1 if self.type in positive_types else -1
        return direction * -1 if cancel else direction


class Wallet(Base):
    __tablename__ = 'wallet'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    name: Mapped[str] = mapped_column(String(255))
    comment: Mapped[str | None] = mapped_column(String(1024))

    # Relationships
    assets: Mapped[list['WalletAsset']] = relationship(back_populates='wallet', lazy='select')
    transactions: Mapped[list['Transaction']] = relationship(back_populates='wallet',
                                          order_by='Transaction.date.desc()')


class WalletAsset(Base):
    __tablename__ = 'wallet_asset'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticker_id: Mapped[str] = mapped_column(String(256))
    wallet_id: Mapped[int] = mapped_column(ForeignKey('wallet.id'))
    quantity: Mapped[Decimal] = mapped_column(Numeric, default=Decimal(0))
    buy_orders: Mapped[Decimal] = mapped_column(Numeric, default=Decimal(0))
    sell_orders: Mapped[Decimal] = mapped_column(Numeric, default=Decimal(0))

    # Relationships
    wallet: Mapped['Wallet'] = relationship(back_populates='assets')
