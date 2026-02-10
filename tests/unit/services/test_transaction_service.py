from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import patch

import pytest

from app.core.exceptions import NotFoundError
from app.services.transaction import TransactionService


@pytest.fixture
async def service(
    db_session,
    transaction_repo,
    portfolio_service,
    portfolio_asset_service,
    wallet_service,
    wallet_asset_service,
):
    service = TransactionService(db_session)

    service.repo = transaction_repo
    service.portfolio_service = portfolio_service
    service.portfolio_asset_service = portfolio_asset_service
    service.wallet_service = wallet_service
    service.wallet_asset_service = wallet_asset_service

    return service


class TestTransactionService:
    async def test_create_transaction_success(self, service, mock, data):
        transaction_data = data(
            date=datetime.now(UTC),
            ticker_id='AAPL',
            ticker2_id='USD',
            quantity=Decimal(10),
            type='Buy',
            portfolio_id=1,
            wallet_id=1,
        )

        transaction = mock(
            date=transaction_data.date,
            ticker_id='AAPL',
            quantity=Decimal(10),
            type='Buy',
        )

        with (
            patch.object(service.repo, 'create', return_value=transaction),
        ):
            result = await service.create_transaction(1, transaction_data)

            assert result.ticker_id == 'AAPL'
            service.repo.create.assert_called_once()
            service.portfolio_service.handle_transaction.assert_called_once_with(1, transaction, cancel=False)
            service.wallet_service.handle_transaction.assert_called_once_with(1, transaction, cancel=False)

    async def test_update_transaction_success(self, service, mock, data):
        transaction_id = 1
        update_data = data(
            date=datetime.now(UTC),
            ticker_id='AAPL',
            ticker2_id='USD',
            quantity=Decimal(10),
            type='Buy',
            portfolio_id=1,
            wallet_id=1,
        )

        existing_transaction = mock(quantity=Decimal(8))
        updated_transaction = mock(quantity=Decimal(10))

        with (
            patch.object(service.repo, 'get', return_value=existing_transaction),
            patch.object(service.repo, 'update', return_value=updated_transaction),
        ):
            result = await service.update_transaction(1, transaction_id, update_data)

            assert len(result) == 2  # Возвращает кортеж (updated, old)
            service.portfolio_service.handle_transaction.assert_any_call(1, existing_transaction, cancel=True)
            service.portfolio_service.handle_transaction.assert_any_call(1, updated_transaction, cancel=False)
            service.wallet_service.handle_transaction.assert_any_call(1, existing_transaction, cancel=True)
            service.wallet_service.handle_transaction.assert_any_call(1, updated_transaction, cancel=False)

    async def test_update_transaction_not_found(self, service, data):
        transaction_id = 999
        update_data = data(
            date=datetime.now(UTC),
            ticker_id='AAPL',
            ticker2_id='USD',
            quantity=Decimal(10),
            type='Buy',
            portfolio_id=1,
            wallet_id=1,
        )

        with (
            patch.object(service.repo, 'get', return_value=None),
            pytest.raises(NotFoundError, match='не найдена'),
        ):
            await service.update_transaction(1, transaction_id, update_data)

    async def test_delete_transaction_success(self, service, mock):
        transaction_id = 1

        transaction = mock(
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
            service.portfolio_service.handle_transaction.assert_called_once_with(1, transaction, cancel=True)
            service.wallet_service.handle_transaction.assert_called_once_with(1, transaction, cancel=True)
            service.repo.delete.assert_called_once_with(1)

    async def test_delete_transaction_not_found(self, service):
        transaction_id = 999

        with (
            patch.object(service.repo, 'get', return_value=None),
            pytest.raises(NotFoundError, match='не найдена'),
        ):
            await service.delete_transaction(1, transaction_id)
