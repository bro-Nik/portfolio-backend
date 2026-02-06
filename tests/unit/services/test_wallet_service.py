from unittest.mock import patch

import pytest
import pytest_asyncio

from app.core.exceptions import ConflictError, NotFoundError
from app.schemas.wallet import WalletResponse
from app.services.wallet import WalletService


class TestWalletService:

    @pytest_asyncio.fixture
    async def service(self, mock_db_session, mock_wallet_repo, mock_wallet_asset_service):
        service = WalletService(mock_db_session)
        service.repo = mock_wallet_repo
        service.asset_service = mock_wallet_asset_service
        return service

    @pytest.mark.asyncio
    async def test_get_wallets_success(self, service, mock):
        wallets = [
            mock(id=1, name='Wallet 1', user_id=1),
            mock(id=2, name='Wallet 2', user_id=1),
        ]

        with (
            patch.object(service.repo, 'get_many_by_user', return_value=wallets),
            patch.object(WalletResponse, 'model_validate', side_effect=wallets),
        ):
            result = await service.get_wallets(1)

            assert len(result) == 2
            assert result[0].name == 'Wallet 1'
            assert result[1].name == 'Wallet 2'
            service.repo.get_many_by_user.assert_called_once_with(1, include_assets=True)

    @pytest.mark.asyncio
    async def test_get_wallet_success(self, service, mock):
        wallet = mock(id=1, name='Test', assets=[mock()])

        with (
            patch.object(service.repo, 'get_by_id_and_user_with_assets', return_value=wallet),
            patch.object(WalletResponse, 'model_validate', return_value=wallet),
        ):
            result = await service.get_wallet(1, 1)

            assert result.id == 1
            assert result.name == 'Test'
            assert len(result.assets) == 1
            service.repo.get_by_id_and_user_with_assets.assert_called_once_with(1, 1)

    @pytest.mark.asyncio
    async def test_get_wallet_not_found(self, service):
        with (
            patch.object(service.repo, 'get_by_id_and_user_with_assets', return_value=None),
            pytest.raises(NotFoundError, match='не найден'),
        ):
            await service.get_wallet(999, 1)

    @pytest.mark.asyncio
    async def test_create_wallet_success(self, service, mock, data):
        wallet_data = data(name='New Wallet')
        wallet = mock(name='New Wallet')

        with (
            patch.object(service.repo, 'exists_by_name_and_user', return_value=False),
            patch.object(service.repo, 'create', return_value=wallet),
            patch.object(service.repo, 'get_by_id_and_user_with_assets', return_value=wallet),
            patch.object(WalletResponse, 'model_validate', return_value=wallet),
        ):
            result = await service.create_wallet(1, wallet_data)

            assert result.name == 'New Wallet'
            service.repo.exists_by_name_and_user.assert_called_once_with('New Wallet', 1)
            service.repo.create.assert_called_once()
            service.session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_wallet_duplicate_name(self, service, data):
        wallet_data = data(name='Existing Wallet')

        with (
            patch.object(service.repo, 'exists_by_name_and_user', return_value=True),
            pytest.raises(ConflictError, match='уже существует'),
        ):
            await service.create_wallet(1, wallet_data)

    @pytest.mark.asyncio
    async def test_update_wallet_success(self, service, mock, data):
        wallet_data = data(name='Updated Name')
        existing_wallet = mock(id=1, name='Old Name', user_id=1)
        updated_wallet = mock(id=1, name='Updated Name', user_id=1)

        with (
            patch.object(service.repo, 'get_by_id_and_user', return_value=existing_wallet),
            patch.object(service.repo, 'exists_by_name_and_user', return_value=False),
            patch.object(service.repo, 'update', return_value=updated_wallet),
            patch.object(WalletResponse, 'model_validate', return_value=updated_wallet),
        ):
            result = await service.update_wallet(1, 1, wallet_data)

            assert result.name == 'Updated Name'
            service.repo.get_by_id_and_user_with_assets.assert_called_with(1, 1)
            service.repo.exists_by_name_and_user.assert_called_once_with('Updated Name', 1)

    @pytest.mark.asyncio
    async def test_delete_wallet_success(self, service, mock):
        wallet = mock(id=1, user_id=1)

        with (
            patch.object(service.repo, 'get_by_id_and_user', return_value=wallet),
            patch.object(service.repo, 'delete', return_value=True),
        ):
            await service.delete_wallet(1, 1)

            service.repo.get_by_id_and_user.assert_called_once_with(1, 1)
            service.repo.delete.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_handle_transaction_trade(self, service, mock):
        transaction = mock(wallet_id=1, type='Buy')
        wallet = mock(id=1, user_id=1)

        with (
            patch.object(service.repo, 'get_by_id_and_user', return_value=wallet),
            patch.object(WalletResponse, 'model_validate', return_value=wallet),
        ):
            await service.handle_transaction(1, transaction)

            service.repo.get_by_id_and_user.assert_called_once_with(1, 1)
            service.asset_service.handle_transaction.assert_called_once_with(transaction, cancel=False)

    @pytest.mark.asyncio
    async def test_handle_transaction_trade_with_cancel(self, service, mock):
        transaction = mock(wallet_id=1, type='Buy')
        wallet = mock(id=1, user_id=1)

        with (
            patch.object(service.repo, 'get_by_id_and_user', return_value=wallet),
            patch.object(WalletResponse, 'model_validate', return_value=wallet),
        ):
            await service.handle_transaction(1, transaction, cancel=True)

            service.repo.get_by_id_and_user.assert_called_once_with(1, 1)
            service.asset_service.handle_transaction.assert_called_once_with(transaction, cancel=True)

    @pytest.mark.asyncio
    async def test_handle_transaction_transfer(self, service, mock):
        transaction = mock(wallet_id=1, wallet2_id=2, type='TransferOut')
        wallet1 = mock(id=1, user_id=1)
        wallet2 = mock(id=2, user_id=1)

        with (
            patch.object(service.repo, 'get_by_id_and_user', side_effect=[wallet1, wallet2]),
        ):
            await service.handle_transaction(1, transaction)

            assert service.repo.get_by_id_and_user.call_count == 2
            service.asset_service.handle_transaction.assert_called_once_with(transaction, cancel=False)

    @pytest.mark.asyncio
    async def test_handle_transaction_transfer_no_wallet2(self, service, mock):
        transaction = mock(wallet_id=1, wallet2_id=None, type='TransferOut')

        await service.handle_transaction(1, transaction)

        service.repo.get_by_id_and_user.assert_not_called()
        service.asset_service.handle_transaction.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_transaction_earning(self, service, mock):
        transaction = mock(wallet_id=1, type='Earning')
        wallet = mock(id=1, user_id=1)

        with (
            patch.object(service.repo, 'get_by_id_and_user', return_value=wallet),
        ):
            await service.handle_transaction(1, transaction)

            service.repo.get_by_id_and_user.assert_called_once_with(1, 1)
            service.asset_service.handle_transaction.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_transaction_input_output(self, service, mock):
        for t_type in ['Input', 'Output']:
            transaction = mock(wallet_id=1, type=t_type)
            wallet = mock(id=1, user_id=1)

            with (
                patch.object(service.repo, 'get_by_id_and_user', return_value=wallet),
            ):

                service.repo.get_by_id_and_user.reset_mock()
                service.asset_service.handle_transaction.reset_mock()

                await service.handle_transaction(1, transaction)

                service.repo.get_by_id_and_user.assert_called_once_with(1, 1)
                service.asset_service.handle_transaction.assert_called_once_with(
                    transaction, cancel=False,
                )
