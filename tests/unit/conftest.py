from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.repositories import (
    PortfolioAssetRepository,
    PortfolioRepository,
    TransactionRepository,
    WalletAssetRepository,
    WalletRepository,
)
from app.services import (
    PortfolioAssetService,
    PortfolioService,
    WalletAssetService,
    WalletService,
)


@pytest.fixture
def db_session() -> AsyncMock:
    """Мок асинхронной сессии БД для unit-тестов."""
    session = AsyncMock()

    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    session.close = AsyncMock()
    session.execute = AsyncMock()
    session.scalar = AsyncMock()

    # Для работы с контекстным менеджером
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)

    return session


@pytest.fixture
def portfolio_repo(db_session) -> MagicMock:
    repo = MagicMock(spec=PortfolioRepository)
    repo.session = db_session
    return repo


@pytest.fixture
def wallet_repo(db_session) -> MagicMock:
    repo = MagicMock(spec=WalletRepository)
    repo.session = db_session
    return repo


@pytest.fixture
def portfolio_asset_repo(db_session) -> MagicMock:
    repo = MagicMock(spec=PortfolioAssetRepository)
    repo.session = db_session
    return repo


@pytest.fixture
def wallet_asset_repo(db_session) -> MagicMock:
    repo = MagicMock(spec=WalletAssetRepository)
    repo.session = db_session
    return repo


@pytest.fixture
def transaction_repo(db_session) -> MagicMock:
    repo = MagicMock(spec=TransactionRepository)
    repo.session = db_session
    return repo


@pytest.fixture
def portfolio_service(db_session, portfolio_repo) -> MagicMock:
    service = MagicMock(spec=PortfolioService)
    service.session = db_session
    service.repo = portfolio_repo
    return service


@pytest.fixture
def wallet_service(db_session, wallet_repo) -> MagicMock:
    service = MagicMock(spec=WalletService)
    service.session = db_session
    service.repo = wallet_repo
    return service


@pytest.fixture
def portfolio_asset_service(db_session, portfolio_asset_repo) -> MagicMock:
    service = MagicMock(spec=PortfolioAssetService)
    service.session = db_session
    service.repo = portfolio_asset_repo
    return service


@pytest.fixture
def wallet_asset_service(db_session, wallet_asset_repo) -> MagicMock:
    service = MagicMock(spec=WalletAssetService)
    service.session = db_session
    service.repo = wallet_asset_repo
    return service


@pytest.fixture
def mock():
    """Создает MagicMock с заданными атрибутами."""
    def _create(**kwargs):
        mock = MagicMock()
        for key, value in kwargs.items():
            setattr(mock, key, value)
        return mock
    return _create


@pytest.fixture
def data():
    """Создает SimpleNamespace с заданными атрибутами."""
    def _create(**kwargs):
        obj = SimpleNamespace(**kwargs)

        def model_dump(**_):
            return {k: getattr(obj, k) for k in kwargs}

        obj.model_dump = model_dump
        return obj
    return _create
