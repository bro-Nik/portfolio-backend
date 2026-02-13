from unittest.mock import patch

import pytest

from app.core.exceptions import ConflictError, NotFoundError
from app.schemas import PortfolioResponse
from app.services import PortfolioService


@pytest.fixture
async def service(db_session, portfolio_repo, portfolio_asset_service):
    service = PortfolioService(db_session)
    service.repo = portfolio_repo
    service.asset_service = portfolio_asset_service
    return service


class TestPortfolioService:
    async def test_get_portfolios_success(self, service, mock):
        portfolios = [
            mock(id=1, name='Test1'),
            mock(id=2, name='Test2'),
        ]

        with (
            patch.object(service.repo, 'get_many_by_user', return_value=portfolios),
            patch('app.services.portfolio.PortfolioListResponse', return_value=portfolios),
        ):
            result = await service.get_many(1)

            assert len(result) == 2
            assert result[0].name == 'Test1'
            assert result[1].name == 'Test2'
            service.repo.get_many_by_user.assert_called_once_with(1, include_assets=True)

    async def test_get_portfolio_success(self, service, mock):
        portfolio = mock(id=1, name='Test', assets=[mock()])

        with (
            patch.object(service.repo, 'get_by_id_and_user', return_value=portfolio),
            patch.object(PortfolioResponse, 'model_validate', return_value=portfolio),
        ):
            result = await service.get(1, 1)

            assert result.id == 1
            assert result.name == 'Test'
            assert len(result.assets) == 1
            service.repo.get_by_id_and_user.assert_called_once_with(1, 1)

    async def test_get_portfolio_not_found(self, service):
        with (
            patch.object(service.repo, 'get_by_id_and_user', return_value=None),
            pytest.raises(NotFoundError, match='не найден'),
        ):
            await service.get(999, 1)

    async def test_create_portfolio_success(self, service, mock, data):
        portfolio_data = data(name='New Portfolio', market='stocks')
        portfolio = mock(name='New Portfolio')

        with (
            patch.object(service.repo, 'exists_by_name_and_user', return_value=False),
            patch.object(service.repo, 'create', return_value=portfolio),
        ):
            result = await service.create(1, portfolio_data)

            assert result.name == 'New Portfolio'
            service.repo.exists_by_name_and_user.assert_called_once_with('New Portfolio', 1)
            service.repo.create.assert_called_once()
            service.session.flush.assert_called_once()

    async def test_create_portfolio_duplicate_name(self, service, data):
        portfolio_data = data(name='Existing Portfolio')

        with (
            patch.object(service.repo, 'exists_by_name_and_user', return_value=True),
            pytest.raises(ConflictError, match='уже существует'),
        ):
            await service.create(1, portfolio_data)

    async def test_update_portfolio_success(self, service, mock, data):
        portfolio_data = data(name='Updated Name')
        existing_portfolio = mock(id=1, name='Old Name', user_id=1)
        updated_portfolio = mock(id=1, name='Updated Name', user_id=1)

        with (
            patch.object(service.repo, 'get_by_id_and_user', return_value=existing_portfolio),
            patch.object(service.repo, 'exists_by_name_and_user', return_value=False),
            patch.object(service.repo, 'update', return_value=updated_portfolio),
            patch.object(PortfolioResponse, 'model_validate', return_value=updated_portfolio),
        ):
            result = await service.update(1, 1, portfolio_data)

            assert result.name == 'Updated Name'
            service.repo.get_by_id_and_user.assert_called_with(1, 1)
            service.repo.exists_by_name_and_user.assert_called_once_with('Updated Name', 1)

    async def test_delete_portfolio_success(self, service, mock):
        portfolio = mock(id=1, user_id=1)

        with (
            patch.object(service.repo, 'get_by_id_and_user', return_value=portfolio),
            patch.object(service.repo, 'delete', return_value=True),
        ):
            await service.delete(1, 1)

            service.repo.get_by_id_and_user.assert_called_once_with(1, 1)
            service.repo.delete.assert_called_once_with(1)

    async def test_add_asset_success(self, service, mock, data):
        """Тест добавления актива в портфель."""
        portfolio_id = 1
        user_id = 1
        asset_data = data(ticker_id='AAPL')

        portfolio = mock(id=portfolio_id, name='Test Portfolio')

        with (
            patch.object(service, 'get', return_value=portfolio),
            patch.object(service.asset_service, 'create', return_value=None),
        ):
            result = await service.add_asset(portfolio_id, user_id, asset_data)

            assert result.id == portfolio_id
            service.asset_service.create.assert_called_once_with(asset_data)
            service.get.assert_called_once_with(portfolio_id, user_id)

    async def test_handle_transaction_trade(self, service, mock):
        transaction = mock(portfolio_id=1, type='Buy')
        portfolio = mock(id=1, user_id=1)

        with (
            patch.object(service.repo, 'get_by_id_and_user', return_value=portfolio),
            patch.object(PortfolioResponse, 'model_validate', return_value=portfolio),
        ):
            await service.handle_transaction(1, transaction)

            service.repo.get_by_id_and_user.assert_called_once_with(1, 1)
            service.asset_service.handle_transaction.assert_called_once_with(transaction, cancel=False)

    async def test_handle_transaction_no_portfolio(self, service, mock):
        transaction = mock(portfolio_id=None, type='Buy')

        await service.handle_transaction(1, transaction)

        service.repo.get_by_id_and_user.assert_not_called()
        service.asset_service.handle_transaction.assert_not_called()
