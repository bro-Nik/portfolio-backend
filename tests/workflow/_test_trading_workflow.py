from datetime import UTC, datetime
from decimal import Decimal

from fastapi import status


class TestTradingWorkflowEndToEnd:
    """Тесты полных торговых сценариев."""

    async def test_complete_trading_workflow(self, client, auth_headers):
        """Полный сценарий: создание портфеля, добавление средств, торговля."""
        auth_headers = {**auth_headers, 'X-Forwarded-For': '192.168.1.10'}

        # Создание портфеля
        portfolio_data = {
            'name': 'Мой инвестиционный портфель',
            'market': 'stock',
            'comment': 'Портфель для торговли акциями',
        }

        portfolio_response = await client.post('/portfolios/', json=portfolio_data, headers=auth_headers)
        assert portfolio_response.status_code == status.HTTP_201_CREATED
        portfolio_id = portfolio_response.json()['id']

        # Создание кошелька
        wallet_data = {
            'name': 'Торговый кошелек USD',
            'comment': 'Основной кошелек для расчетов',
        }

        wallet_response = await client.post('/wallets/', json=wallet_data, headers=auth_headers)
        assert wallet_response.status_code == status.HTTP_201_CREATED
        wallet_id = wallet_response.json()['id']

        # Пополнение кошелька
        funding_transaction = {
            'date': datetime.now(UTC).isoformat(),
            'ticker_id': 'USD',
            'quantity': '100000.0',
            'type': 'Input',
            'wallet_id': wallet_id,
            'comment': 'Начальное пополнение',
        }

        funding_response = await client.post('/transactions/', json=funding_transaction, headers=auth_headers)
        assert funding_response.status_code == status.HTTP_200_OK

        # Добавление активов в портфель
        tickers = ['AAPL', 'GOOGL', 'MSFT']

        for ticker in tickers:
            asset_data = {'ticker_id': ticker, 'portfolio_id': portfolio_id}
            response = await client.post(f'/portfolios/{portfolio_id}/assets', json=asset_data, headers=auth_headers)
            assert response.status_code == status.HTTP_201_CREATED

        # Покупка акций
        trades = [
            {'ticker': 'AAPL', 'quantity': 10, 'price': 150.0},
            {'ticker': 'GOOGL', 'quantity': 5, 'price': 2800.0},
            {'ticker': 'MSFT', 'quantity': 8, 'price': 350.0},
        ]

        for trade in trades:
            transaction_data = {
                'date': datetime.now(UTC).isoformat(),
                'ticker_id': trade['ticker'],
                'ticker2_id': 'USD',
                'quantity': str(trade['quantity']),
                'quantity2': str(trade['quantity'] * trade['price']),
                'price': str(trade['price']),
                'price_usd': str(trade['price']),
                'type': 'Buy',
                'portfolio_id': portfolio_id,
                'wallet_id': wallet_id,
                'comment': f"Покупка {trade['ticker']}",
            }

            response = await client.post('/transactions/', json=transaction_data, headers=auth_headers)
            assert response.status_code == status.HTTP_200_OK

        # Проверка состояния портфеля
        portfolio_response = await client.get(f'/portfolios/{portfolio_id}', headers=auth_headers)
        assert portfolio_response.status_code == status.HTTP_200_OK

        portfolio = portfolio_response.json()

        total_value = Decimal(0)
        for asset in portfolio['assets']:
            value = Decimal(asset['amount'])
            total_value += value

        # Проверка состояния кошелька
        wallet_response = await client.get(f'/wallets/{wallet_id}', headers=auth_headers)
        assert wallet_response.status_code == status.HTTP_200_OK

        wallet = wallet_response.json()
        usd_asset = next((a for a in wallet['assets'] if a['ticker_id'] == 'USD'), None)

        if usd_asset:
            remaining_usd = Decimal(usd_asset['quantity'])

            # Проверяем что потратили правильную сумму
            total_spent = Decimal(100000) - remaining_usd
            expected_spent = sum(trade['quantity'] * trade['price'] for trade in trades)
            assert abs(total_spent - Decimal(str(expected_spent))) < Decimal('0.01')

        # Продажа части позиции
        sell_transaction = {
            'date': datetime.now(UTC).isoformat(),
            'ticker_id': 'AAPL',
            'ticker2_id': 'USD',
            'quantity': '3.0',
            'quantity2': '480.0',  # 3 * 160
            'price': '160.0',
            'price_usd': '160.0',
            'type': 'Sell',
            'portfolio_id': portfolio_id,
            'wallet_id': wallet_id,
            'comment': 'Продажа части AAPL с прибылью',
        }

        sell_response = await client.post('/transactions/', json=sell_transaction, headers=auth_headers)
        assert sell_response.status_code == status.HTTP_200_OK

        # Финансовый результат

        # Получаем обновленный портфель
        portfolio_response = await client.get(f'/portfolios/{portfolio_id}', headers=auth_headers)
        portfolio = portfolio_response.json()

        aapl_asset = next((a for a in portfolio['assets'] if a['ticker_id'] == 'AAPL'), None)
        assert aapl_asset is not None
        assert Decimal(aapl_asset['quantity']) == Decimal('7.0')  # 10 - 3

        # Итоговые проверки
        assert len(portfolio['assets']) == 4
        assert portfolio['name'] == 'Мой инвестиционный портфель'

    async def test_portfolio_rebalancing_workflow(self, client, auth_headers):
        """Сценарий ребалансировки портфеля."""
        auth_headers = {**auth_headers, 'X-Forwarded-For': '192.168.1.11'}

        # Создание портфеля с несколькими активами
        portfolio_data = {'name': 'Сбалансированный портфель', 'market': 'stock'}
        portfolio_response = await client.post('/portfolios/', json=portfolio_data, headers=auth_headers)
        portfolio_id = portfolio_response.json()['id']

        # Добавление активов
        assets = [
            {'ticker': 'BONDS', 'target': 40},  # 40% облигации
            {'ticker': 'STOCKS', 'target': 40},  # 40% акции
            {'ticker': 'GOLD', 'target': 20},    # 20% золото
        ]

        for asset in assets:
            await client.post(
                f'/portfolios/{portfolio_id}/assets',
                json={'ticker_id': asset['ticker'], 'portfolio_id': portfolio_id},
                headers=auth_headers,
            )

        # Начальные инвестиции
        initial_investment = 100000
        # auth_headers = {**auth_headers, 'X-Forwarded-For': '192.168.1.12'}
        for asset in assets:
            amount = initial_investment * (asset['target'] / 100)
            transaction_data = {
                'date': datetime.now(UTC).isoformat(),
                'ticker_id': asset['ticker'],
                'quantity': str(amount / 100),  # Упрощенная модель
                'price': '100.0',
                'price_usd': '100.0',
                'type': 'Buy',
                'portfolio_id': portfolio_id,
                'comment': f"Начальная покупка {asset['ticker']}",
            }
            await client.post('/transactions/', json=transaction_data, headers=auth_headers)

        # Проверка начального распределения
        portfolio_response = await client.get(f'/portfolios/{portfolio_id}', headers=auth_headers)
        portfolio = portfolio_response.json()
        print(portfolio)

        for asset in portfolio['assets']:
            percentage = (Decimal(asset['amount']) / Decimal(initial_investment)) * 100

        # Симуляция изменения цен (акции выросли на 20%)

        # Находим акции STOCKS
        stocks_asset = next(a for a in portfolio['assets'] if a['ticker_id'] == 'STOCKS')
        stocks_amount = Decimal(stocks_asset['amount'])
        new_stocks_amount = stocks_amount * Decimal('1.2')

        # "Корректирующая" транзакция (в реальности это были бы несколько сделок)
        rebalance_transaction = {
            'date': datetime.now(UTC).isoformat(),
            'ticker_id': 'STOCKS',
            'ticker2_id': 'BONDS',
            'quantity': str((new_stocks_amount - stocks_amount) / Decimal(120)),  # Новая цена
            'quantity2': str((new_stocks_amount - stocks_amount) / Decimal(100)),  # Старая цена облигаций
            'price': '120.0',
            'price_usd': '120.0',
            'type': 'Sell',
            'portfolio_id': portfolio_id,
            'comment': 'Ребалансировка: продажа части акций',
        }

        response = await client.post('/transactions/', json=rebalance_transaction, headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK

        # Проверка конечного распределения
        portfolio_response = await client.get(f'/portfolios/{portfolio_id}', headers=auth_headers)
        portfolio = portfolio_response.json()

        total_amount = sum(Decimal(a['amount']) for a in portfolio['assets'])

        for asset in portfolio['assets']:
            percentage = (Decimal(asset['amount']) / total_amount) * 100
