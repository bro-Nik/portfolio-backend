from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from app.repositories.transaction import TransactionRepository
from app.repositories.wallet import WalletRepository
from app.repositories.wallet_asset import WalletAssetRepository
from app.services.portfolio import PortfolioService
from app.services.wallet import WalletService
from app.services.wallet_asset import WalletAssetService
import pytest

from app.repositories import PortfolioRepository
from app.repositories.portfolio_asset import AssetRepository
from app.services.portfolio_asset import PortfolioAssetService


@pytest.fixture
def mock_db_session() -> AsyncMock:
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
def mock_portfolio_repo(mock_db_session) -> MagicMock:
    repo = MagicMock(spec=PortfolioRepository)
    repo.session = mock_db_session
    return repo


@pytest.fixture
def mock_wallet_repo(mock_db_session) -> MagicMock:
    repo = MagicMock(spec=WalletRepository)
    repo.session = mock_db_session
    return repo


@pytest.fixture
def mock_portfolio_asset_repo(mock_db_session) -> MagicMock:
    repo = MagicMock(spec=AssetRepository)
    repo.session = mock_db_session
    return repo


@pytest.fixture
def mock_wallet_asset_repo(mock_db_session) -> MagicMock:
    repo = MagicMock(spec=WalletAssetRepository)
    repo.session = mock_db_session
    return repo


@pytest.fixture
def mock_transaction_repo(mock_db_session) -> MagicMock:
    repo = MagicMock(spec=TransactionRepository)
    repo.session = mock_db_session
    return repo


@pytest.fixture
def mock_portfolio_service(mock_db_session, mock_portfolio_repo) -> MagicMock:
    service = MagicMock(spec=PortfolioService)
    service.session = mock_db_session
    service.repo = mock_portfolio_repo
    return service


@pytest.fixture
def mock_wallet_service(mock_db_session, mock_wallet_repo) -> MagicMock:
    service = MagicMock(spec=WalletService)
    service.session = mock_db_session
    service.repo = mock_wallet_repo
    return service


@pytest.fixture
def mock_portfolio_asset_service(mock_db_session, mock_portfolio_asset_repo) -> MagicMock:
    service = MagicMock(spec=PortfolioAssetService)
    service.session = mock_db_session
    service.repo = mock_portfolio_asset_repo
    return service


@pytest.fixture
def mock_wallet_asset_service(mock_db_session, mock_wallet_asset_repo) -> MagicMock:
    service = MagicMock(spec=WalletAssetService)
    service.session = mock_db_session
    service.repo = mock_wallet_asset_repo
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
