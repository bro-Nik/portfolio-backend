from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import patch

import pytest

from app.core.exceptions import ConflictError, NotFoundError
from app.schemas.portfolio_asset import PortfolioAssetResponse
from app.services.portfolio_asset import PortfolioAssetService


@pytest.fixture
async def service(mock_db_session, mock_portfolio_asset_repo):
    service = PortfolioAssetService(mock_db_session)
    service.repo = mock_portfolio_asset_repo
    return service


class TestPortfolioAssetService:
    async def test_create_asset_success(self, service, mock, data):
        asset_data = data(ticker_id='AAPL', portfolio_id=1)
        asset = mock(id=1, ticker_id='AAPL', portfolio_id=1, quantity=Decimal(0))

        with (
            patch.object(service.repo, 'get_by_ticker_and_portfolio', return_value=None),
            patch.object(service.repo, 'create', return_value=asset),
            patch.object(PortfolioAssetResponse, 'model_validate', return_value=asset),
        ):
            result = await service.create_asset(asset_data)

            assert result.ticker_id == 'AAPL'
            service.repo.get_by_ticker_and_portfolio.assert_called_once_with('AAPL', 1)
            service.repo.create.assert_called_once()
            service.session.flush.assert_called_once()

    async def test_create_asset_already_exists(self, service, mock, data):
        asset_data = data(ticker_id='AAPL', portfolio_id=1)
        existing_asset = mock(id=1, ticker_id='AAPL', portfolio_id=1)

        with (
            patch.object(service.repo, 'get_by_ticker_and_portfolio', return_value=existing_asset),
            pytest.raises(ConflictError, match='уже добавлен'),
        ):
            await service.create_asset(asset_data)

    async def test_delete_asset_success(self, service):
        with (
            patch.object(service.repo, 'delete', return_value=True),
        ):
            result = await service.delete_asset(1)

            assert result is True
            service.repo.delete.assert_called_once_with(1)

    async def test_get_asset_detail_success(self, service, mock):
        transaction = mock(
            date=datetime.now(UTC),
            ticker_id='AAPL',
            quantity=Decimal('10.0'),
            type='Buy',
        )

        asset = mock(
            ticker_id='AAPL',
            quantity=Decimal('10.0'),
            amount=Decimal('1500.0'),
            transactions=[transaction],
        )

        mock_distribution = {'test_data': 'test_data'}

        with (
            patch.object(service.repo, 'get_by_id_and_user_with_details', return_value=asset),
            patch.object(service, '_calculate_portfolio_distribution', return_value=mock_distribution),
        ):
            result = await service.get_asset_detail(1, 1)

            assert len(result.transactions) == 1
            assert result.transactions[0]['ticker_id'] == 'AAPL'
            assert result.distribution == mock_distribution
            service.repo.get_by_id_and_user_with_details.assert_called_once_with(1, 1)

    async def test_get_asset_detail_not_found(self, service):
        with (
            patch.object(service.repo, 'get_by_id_and_user_with_details', return_value=None),
            pytest.raises(NotFoundError, match='не найден'),
        ):
            await service.get_asset_detail(999, 1)


    async def test_calculate_portfolio_distribution(self, service, mock):
        ticker_id = 'AAPL'
        user_id = 1

        portfolio1 = mock(id=1, name='Portfolio 1')
        portfolio2 = mock(id=2, name='Portfolio 2')

        assets = [
            mock(portfolio=portfolio1, quantity=Decimal('10.0'), amount=Decimal('1500.0')),
            mock(portfolio=portfolio2, quantity=Decimal('5.0'), amount=Decimal('750.0')),
        ]

        with (
            patch.object(service.repo, 'get_many_by_ticker_and_user', return_value=assets),
        ):
            result = await service._calculate_portfolio_distribution(ticker_id, user_id)

        assert result['total_quantity_all_portfolios'] == Decimal('15.0')
        assert result['total_amount_all_portfolios'] == Decimal('2250.0')
        assert len(result['portfolios']) == 2

        portfolio1_data = result['portfolios'][0]
        portfolio2_data = result['portfolios'][1]

        assert portfolio1_data['portfolio_id'] == 1
        assert portfolio1_data['portfolio_name'] == 'Portfolio 1'
        assert portfolio1_data['quantity'] == Decimal('10.0')
        assert portfolio1_data['percentage_of_total'] == 66.67

        assert portfolio2_data['portfolio_id'] == 2
        assert portfolio2_data['portfolio_name'] == 'Portfolio 2'
        assert portfolio2_data['quantity'] == Decimal('5.0')
        assert portfolio2_data['percentage_of_total'] == 33.33

    async def test_calculate_portfolio_distribution_zero_quantity(self, service, mock):
        ticker_id = 'AAPL'
        user_id = 1

        portfolio = mock(id=1)
        asset = mock(portfolio=portfolio, quantity=Decimal('0.0'), amount=Decimal('0.0'))

        with (
            patch.object(service.repo, 'get_many_by_ticker_and_user', return_value=[asset]),
        ):
            result = await service._calculate_portfolio_distribution(ticker_id, user_id)

        assert result['total_quantity_all_portfolios'] == 0.0
        assert result['portfolios'][0]['percentage_of_total'] == 0.0

    async def test_handle_transaction_trade_execution(self, service, mock):
        transaction = mock(
            ticker_id='AAPL',
            ticker2_id='USD',
            quantity=Decimal('10.0'),
            quantity2=Decimal('1500.0'),
            price=Decimal('150.0'),
            price_usd=Decimal('150.0'),
            type='Buy',
            order=False,
        )
        transaction.get_direction.return_value = 1

        asset1 = mock(ticker_id='AAPL', quantity=Decimal(0), amount=Decimal(0))
        asset2 = mock(ticker_id='USD', quantity=Decimal(10000), amount=Decimal(0))

        with (
            patch.object(service.repo, 'get_or_create', side_effect=[asset1, asset2]),
        ):
            await service.handle_transaction(transaction)

        assert asset1.quantity == Decimal(10)  # AAPL добавлено
        assert asset1.amount == Decimal(1500)  # 10 * 150
        assert asset2.quantity == Decimal(8500)  # USD потрачено (10000 - 1500)

    async def test_handle_transaction_trade_order(self, service, mock):
        transaction = mock(
            ticker_id='AAPL',
            ticker2_id='USD',
            quantity=Decimal('10.0'),
            quantity2=Decimal('1500.0'),
            price=Decimal('150.0'),
            price_usd=Decimal('150.0'),
            type='Buy',
            order=True,
        )
        transaction.get_direction.return_value = 1

        asset1 = mock(ticker_id='AAPL', buy_orders=Decimal(0))
        asset2 = mock(ticker_id='USD', sell_orders=Decimal(0))

        with (
            patch.object(service.repo, 'get_or_create', side_effect=[asset1, asset2]),
        ):
            await service.handle_transaction(transaction)

        # Ордеры на покупку
        assert asset1.buy_orders == Decimal('1500.0')  # 10 * 150
        assert asset2.sell_orders == Decimal('-1500.0')

        # Ордеры на продажу
        transaction.type = 'Sell'
        transaction.order = True

        asset3 = mock(ticker_id='AAPL', sell_orders=Decimal(0))
        asset4 = mock(ticker_id='USD', sell_orders=Decimal(0))

        with (
            patch.object(service.repo, 'get_or_create', side_effect=[asset3, asset4]),
        ):
            await service.handle_transaction(transaction)

        assert asset3.sell_orders == Decimal('-10.0')

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
        transaction = mock(quantity=Decimal('1.0'), type='TransferOut')
        transaction.get_direction.return_value = -1

        asset1 = mock(quantity=Decimal('5.0'), amount=Decimal('50000.0'))
        asset2 = mock(quantity=Decimal('2.0'), amount=Decimal('20000.0'))

        with (
            patch.object(service.repo, 'get_or_create', side_effect=[asset1, asset2]),
        ):
            await service.handle_transaction(transaction)

        assert asset1.quantity == Decimal('4.0')  # 5 - 1
        assert asset1.amount == Decimal('40000.0')  # 50000 - (50000/5*1)
        assert asset2.quantity == Decimal('3.0')  # 2 + 1
        assert asset2.amount == Decimal('30000.0')  # 20000 + (50000/5*1)

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

        # Отмена вывода
        transaction.type = 'Output'
        transaction.quantity = Decimal('2000.0')
        transaction.get_direction.return_value = 1

        asset.quantity = Decimal('10000.0')

        with (
            patch.object(service.repo, 'get_or_create', return_value=asset),
        ):
            await service.handle_transaction(transaction, cancel=True)

        assert asset.quantity == Decimal('12000.0')  # 10000 + 2000

    async def test_get_assets_by_portfolio_and_tickers(self, service, mock):
        portfolio_id = 1
        ticker_ids = ['AAPL', 'GOOGL']

        assets = [
            mock(ticker_id='AAPL', portfolio_id=1),
            mock(ticker_id='GOOGL', portfolio_id=1),
        ]

        with (
            patch.object(service.repo, 'get_many_by_tickers_and_portfolio', return_value=assets),
        ):
            result = await service.get_assets_by_portfolio_and_tickers(portfolio_id, ticker_ids)

            assert len(result) == 2
            service.repo.get_many_by_tickers_and_portfolio.assert_called_once_with(ticker_ids, portfolio_id)

    async def test_get_assets_by_portfolio_and_tickers_empty(self, service):
        portfolio_id = 1
        ticker_ids = []

        result = await service.get_assets_by_portfolio_and_tickers(portfolio_id, ticker_ids)

        assert result == []
        service.repo.get_many_by_tickers_and_portfolio.assert_not_called()
