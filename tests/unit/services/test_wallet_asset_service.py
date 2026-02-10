from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import patch

import pytest

from app.core.exceptions import NotFoundError
from app.schemas import WalletAssetDetailResponse
from app.services.wallet_asset import WalletAssetService


@pytest.fixture
async def service(db_session, wallet_asset_repo):
    service = WalletAssetService(db_session)
    service.repo = wallet_asset_repo
    return service


class TestWalletAssetService:
    async def test_get_asset_detail_success(self, service, mock):
        transaction = mock(
            date=datetime.now(UTC),
            ticker_id='USD',
            quantity=Decimal('1000.0'),
            type='Input',
        )

        asset = mock(
            ticker_id='USD',
            quantity=Decimal('10000.0'),
            transactions=[transaction],
        )

        mock_distribution = {'test_data': 'test_data'}

        with (
            patch.object(service.repo, 'get_by_id_and_user_with_details', return_value=asset),
            patch.object(service, '_calculate_wallet_distribution', return_value=mock_distribution),
        ):
            result = await service.get_asset_detail(1, 1)

            assert isinstance(result, WalletAssetDetailResponse)
            assert len(result.transactions) == 1
            assert result.transactions[0]['ticker_id'] == 'USD'
            assert result.distribution == mock_distribution
            service.repo.get_by_id_and_user_with_details.assert_called_once_with(1, 1)

    async def test_get_asset_detail_not_found(self, service):
        with (
            patch.object(service.repo, 'get_by_id_and_user_with_details', return_value=None),
            pytest.raises(NotFoundError, match='не найден'),
        ):
            await service.get_asset_detail(999, 1)

    async def test_calculate_wallet_distribution(self, service, mock):
        ticker_id = 'USD'
        user_id = 1

        wallet1 = mock(id=1, name='Wallet 1')
        wallet2 = mock(id=2, name='Wallet 2')

        assets = [
            mock(wallet=wallet1, quantity=Decimal('7000.0')),
            mock(wallet=wallet2, quantity=Decimal('3000.0')),
        ]

        with (
            patch.object(service.repo, 'get_many_by_ticker_and_user', return_value=assets),
        ):
            result = await service._calculate_wallet_distribution(ticker_id, user_id)

        assert result['total_quantity_all_wallets'] == Decimal('10000.0')
        assert len(result['wallets']) == 2

        wallet1_data = result['wallets'][0]
        wallet2_data = result['wallets'][1]

        assert wallet1_data['wallet_id'] == 1
        assert wallet1_data['wallet_name'] == 'Wallet 1'
        assert wallet1_data['quantity'] == Decimal('7000.0')
        assert wallet1_data['percentage_of_total'] == 70.0

        assert wallet2_data['wallet_id'] == 2
        assert wallet2_data['wallet_name'] == 'Wallet 2'
        assert wallet2_data['quantity'] == Decimal('3000.0')
        assert wallet2_data['percentage_of_total'] == 30.0

    async def test_calculate_wallet_distribution_zero_quantity(self, service, mock):
        ticker_id = 'USD'
        user_id = 1

        wallet = mock(id=1)
        asset = mock(wallet=wallet, quantity=Decimal('0.0'))

        with (
            patch.object(service.repo, 'get_many_by_ticker_and_user', return_value=[asset]),
        ):
            result = await service._calculate_wallet_distribution(ticker_id, user_id)

        assert result['total_quantity_all_wallets'] == Decimal('0.0')
        assert result['wallets'][0]['percentage_of_total'] == 0.0

    async def test_handle_transaction_trade_execution(self, service, mock):
        transaction = mock(
            ticker_id='BTC',
            ticker2_id='USD',
            quantity=Decimal('1.0'),
            quantity2=Decimal('50000.0'),
            type='Buy',
            order=False,
        )
        transaction.get_direction.return_value = 1

        asset1 = mock(ticker_id='BTC', quantity=Decimal(0))
        asset2 = mock(ticker_id='USD', quantity=Decimal(100000))

        with (
            patch.object(service.repo, 'get_or_create', side_effect=[asset1, asset2]),
        ):
            await service.handle_transaction(transaction)

        assert asset1.quantity == Decimal('1.0')  # BTC добавлено
        assert asset2.quantity == Decimal('50000.0')  # USD потрачено (10000 - 1500)

    async def test_handle_transaction_trade_order(self, service, mock):
        transaction = mock(
            ticker_id='BTC',
            ticker2_id='USD',
            quantity=Decimal('1.0'),
            quantity2=Decimal('50000.0'),
            price=Decimal('50000.0'),
            price_usd=Decimal('50000.0'),
            type='Buy',
            order=True,
        )
        transaction.get_direction.return_value = 1

        asset1 = mock(ticker_id='BTC', buy_orders=Decimal(0))
        asset2 = mock(ticker_id='USD', sell_orders=Decimal(0))

        with (
            patch.object(service.repo, 'get_or_create', side_effect=[asset1, asset2]),
        ):
            await service.handle_transaction(transaction)

        # Ордеры на покупку
        assert asset1.buy_orders == Decimal('50000.0')
        assert asset2.sell_orders == Decimal('-50000.0')

        # Ордеры на продажу
        transaction.type = 'Sell'

        asset3 = mock(ticker_id='BTC', sell_orders=Decimal(0))
        asset4 = mock(ticker_id='USD', sell_orders=Decimal(0))

        with (
            patch.object(service.repo, 'get_or_create', side_effect=[asset3, asset4]),
        ):
            await service.handle_transaction(transaction)

        assert asset3.sell_orders == Decimal('-1.0')

    async def test_handle_transaction_earning(self, service, mock):
        transaction = mock(
            ticker_id='USD',
            quantity=Decimal('1000.0'),
            type='Earning',
        )
        transaction.get_direction.return_value = 1

        asset = mock(ticker_id='USD', quantity=Decimal(0))

        with (
            patch.object(service.repo, 'get_or_create', return_value=asset),
        ):
            await service.handle_transaction(transaction)

        assert asset.quantity == Decimal('1000.0')

    async def test_handle_transaction_transfer(self, service, mock):
        transaction = mock(quantity=Decimal('0.5'), type='TransferOut')
        transaction.get_direction.return_value = -1

        asset1 = mock(quantity=Decimal('2.0'))
        asset2 = mock(quantity=Decimal('1.0'))

        with (
            patch.object(service.repo, 'get_or_create', side_effect=[asset1, asset2]),
        ):
            await service.handle_transaction(transaction)

        assert asset1.quantity == Decimal('1.5')  # 2 - 0.5
        assert asset2.quantity == Decimal('1.5')  # 1 + 0.5

    async def test_handle_transaction_transfer_no_wallet2(self, service, mock):
        transaction = mock(
            ticker_id='BTC',
            quantity=Decimal('0.5'),
            type='TransferOut',
            wallet_id=1,
            wallet2_id=None,  # No target wallet
        )

        await service.handle_transaction(transaction)

        service.repo.get_or_create.assert_not_called()

    async def test_handle_transaction_input_output(self, service, mock):
        # Ввод
        transaction = mock(quantity=Decimal('5000.0'), type='Input')
        transaction.get_direction.return_value = 1

        asset = mock(quantity=Decimal(0))

        with (
            patch.object(service.repo, 'get_or_create', return_value=asset),
        ):
            await service.handle_transaction(transaction)

        assert asset.quantity == Decimal('5000.0')

        # Вывод
        transaction.type = 'Output'
        transaction.quantity = Decimal('2000.0')
        transaction.get_direction.return_value = -1

        asset.quantity = Decimal('10000.0')

        with (
            patch.object(service.repo, 'get_or_create', return_value=asset),
        ):
            await service.handle_transaction(transaction)

        assert asset.quantity == Decimal('8000.0')  # 10000 - 2000

    async def test_handle_transaction_with_cancel(self, service, mock):
        # Arrange
        transaction = mock(
            ticker_id='BTC',
            ticker2_id='USDT',
            quantity=Decimal('1.0'),
            quantity2=Decimal('20000.0'),
            type='Buy',
            wallet_id=1,
            order=False,
        )
        transaction.get_direction.return_value = -1

        asset1 = mock(ticker_id='BTC', quantity=Decimal('5.0'))
        asset2 = mock(ticker_id='USD', quantity=Decimal(100000))

        with (
            patch.object(service.repo, 'get_or_create', side_effect=[asset1, asset2]),
        ):
            await service.handle_transaction(transaction, cancel=True)

        assert asset1.quantity == Decimal('4.0')  # 5 - 1
        assert asset2.quantity == Decimal('120000.0')  # 5 - 1

    async def test_get_assets_by_wallet_and_tickers(self, service, mock):
        wallet_id = 1
        ticker_ids = ['USD', 'EUR']

        assets = [
            mock(ticker_id='USD', wallet_id=1),
            mock(ticker_id='EUR', wallet_id=1),
        ]

        with (
            patch.object(service.repo, 'get_many_by_tickers_and_wallet', return_value=assets),
        ):
            result = await service.get_assets_by_wallet_and_tickers(wallet_id, ticker_ids)

            assert len(result) == 2
            service.repo.get_many_by_tickers_and_wallet.assert_called_once_with(ticker_ids, wallet_id)

    async def test_get_assets_by_wallet_and_tickers_empty(self, service):
        wallet_id = 1
        ticker_ids = []

        result = await service.get_assets_by_wallet_and_tickers(wallet_id, ticker_ids)

        assert result == []
        service.repo.get_many_by_tickers_and_wallet.assert_not_called()
