from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import patch

import pytest
import pytest_asyncio

from app.core.exceptions import NotFoundError
from app.models import Transaction
from app.services.transaction import TransactionService


class TestTransactionService:
    @pytest_asyncio.fixture
    async def service(
        self,
        mock_db_session,
        mock_transaction_repo,
        mock_portfolio_service,
        mock_portfolio_asset_service,
        mock_wallet_service,
        mock_wallet_asset_service,
    ):
        service = TransactionService(mock_db_session)

        service.repo = mock_transaction_repo
        service.portfolio_service = mock_portfolio_service
        service.portfolio_asset_service = mock_portfolio_asset_service
        service.wallet_service = mock_wallet_service
        service.wallet_asset_service = mock_wallet_asset_service

        return service

    @pytest.mark.asyncio
    async def test_create_transaction_success(self, service, mock, data):
        transaction_data = data(date=datetime.now(UTC), ticker_id='AAPL', quantity=Decimal(10), type='Buy')
        transaction = mock(date=transaction_data.date, ticker_id='AAPL', quantity=Decimal(10), type='Buy')

        with (
            patch.object(service.repo, 'create', return_value=transaction),
        ):
            result = await service.create_transaction(1, transaction_data)

            assert result.ticker_id == 'AAPL'
            service.repo.create.assert_called_once()
            service.portfolio_service.handle_transaction.assert_called_once_with(1, transaction)
            service.wallet_service.handle_transaction.assert_called_once_with(1, transaction)

    @pytest.mark.asyncio
    async def test_update_transaction_success(self, service, mock, data):
        transaction_id = 1
        update_data = data(date=datetime.now(UTC), ticker_id='AAPL', quantity=Decimal(10), type='Buy')

        existing_transaction = mock(
            id=1,
            ticker_id='AAPL',
            quantity=Decimal(10),
            type='Buy',
            portfolio_id=1,
        )

        updated_transaction = mock(
            id=1,
            ticker_id='AAPL',
            quantity=Decimal(10),
            type='Buy',
            portfolio_id=1,
        )

        with (
            patch.object(service.repo, 'get', return_value=existing_transaction),
            patch.object(service.repo, 'update', return_value=updated_transaction),
        ):
            result = await service.update_transaction(1, transaction_id, update_data)

            assert len(result) == 2  # Возвращает кортеж (updated, old)
            service.portfolio_service.handle_transaction.assert_any_call(1, existing_transaction, cancel=True)
            service.portfolio_service.handle_transaction.assert_any_call(1, updated_transaction)
            service.wallet_service.handle_transaction.assert_any_call(1, existing_transaction, cancel=True)
            service.wallet_service.handle_transaction.assert_any_call(1, updated_transaction)

    @pytest.mark.asyncio
    async def test_update_transaction_not_found(self, service, data):
        transaction_id = 999
        update_data = data(date=datetime.now(UTC), ticker_id='AAPL', quantity=Decimal(10), type='Buy')

        with (
            patch.object(service.repo, 'get', return_value=None),
            pytest.raises(NotFoundError, match='не найдена'),
        ):
            await service.update_transaction(1, transaction_id, update_data)

    @pytest.mark.asyncio
    async def test_delete_transaction_success(self, service):
        transaction_id = 1

        transaction = Transaction(
            id=1,
            ticker_id='AAPL',
            quantity=Decimal(10),
            type='Buy',
            portfolio_id=1,
        )

        with (
            patch.object(service.repo, 'get', return_value=transaction),
            patch.object(service.repo, 'delete', return_value=True),
        ):
            result = await service.delete_transaction(1, transaction_id)

            assert result == transaction
            service.portfolio_service.handle_transaction.assert_called_once_with(
                1, transaction, cancel=True,
            )
            service.wallet_service.handle_transaction.assert_called_once_with(
                1, transaction, cancel=True,
            )
            service.repo.delete.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_delete_transaction_not_found(self, service):
        transaction_id = 999

        with (
            patch.object(service.repo, 'get', return_value=None),
            pytest.raises(NotFoundError, match='не найдена'),
        ):
            await service.delete_transaction(1, transaction_id)
