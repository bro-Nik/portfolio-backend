from datetime import UTC, datetime
from decimal import Decimal

from fastapi import status


class TestTransactionsAPI:
    async def test_create_transaction_buy_crypto(self, client, auth_headers, db_session, portfolio, wallet):
        transaction_data = {
            'date': datetime.now(UTC).isoformat(),
            'ticker_id': 'BTC',
            'ticker2_id': 'USDT',
            'quantity': '0.1',
            'quantity2': '6000.0',  # 0.1 BTC * $60,000 = $6,000 USDT
            'price': '60000.0',  # Цена в USDT
            'price_usd': '59500.0',  # Немного отличается
            'type': 'Buy',
            'portfolio_id': portfolio.id,
            'wallet_id': wallet.id,
            'comment': 'Покупка BTC',
        }

        response = await client.post('/transactions/', json=transaction_data, headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data['success'] is True
        assert 'транзакция успешно создана' in data.get('message', '').lower()

        # Проверяем что активы обновились
        assert data['portfolio_assets'] is not None
        assert len(data['portfolio_assets']) > 0

        # Проверяем что в портфеле появился актив
        data_portfolio = (await client.get(f'/portfolios/{portfolio.id}', headers=auth_headers)).json()
        btc = next((a for a in data_portfolio['assets'] if a['ticker_id'] == 'BTC'), {})
        usdt = next((a for a in data_portfolio['assets'] if a['ticker_id'] == 'USDT'), {})
        assert Decimal(btc['quantity']) == Decimal('0.1')  # Купили 0.1 BTC
        assert Decimal(usdt['quantity']) == Decimal('-6000.0')  # Потратили 6000 USDT

        # Проверяем что в кошельке появился актив
        data_wallet = (await client.get(f'/wallets/{wallet.id}', headers=auth_headers)).json()
        btc = next((a for a in data_wallet['assets'] if a['ticker_id'] == 'BTC'), {})
        usdt = next((a for a in data_wallet['assets'] if a['ticker_id'] == 'USDT'), {})
        assert Decimal(btc['quantity']) == Decimal('0.1')
        assert Decimal(usdt['quantity']) == Decimal('-6000.0')

    async def test_create_transaction_sell_crypto(self, client, auth_headers, portfolio, wallet, portfolio_asset):
        sell_transaction = {
            'date': datetime.now(UTC).isoformat(),
            'ticker_id': 'ETH',
            'ticker2_id': 'USDT',
            'quantity': '2.5',
            'quantity2': '7500.0',  # 2.5 ETH * $3,000 = $7,500 USDT
            'price': '3000.0',  # Цена в USDT
            'price_usd': '2990.0',
            'type': 'Sell',
            'portfolio_id': portfolio.id,
            'wallet_id': wallet.id,
            'comment': 'Продажа части позиции',
        }

        response = await client.post('/transactions/', json=sell_transaction, headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK

        # Проверяем что в портфеле количество уменьшилось
        data_portfolio = (await client.get(f'/portfolios/{portfolio.id}', headers=auth_headers)).json()
        eth = next((a for a in data_portfolio['assets'] if a['ticker_id'] == 'ETH'), {})
        usdt = next((a for a in data_portfolio['assets'] if a['ticker_id'] == 'USDT'), {})
        assert Decimal(eth['quantity']) == Decimal('-2.5')  # Продали 2.5 ETH
        assert Decimal(usdt['quantity']) == Decimal('7500.0')  # Получили 7500 USDT

        # Проверяем что в кошельке количество уменьшилось
        data_wallet = (await client.get(f'/wallets/{wallet.id}', headers=auth_headers)).json()
        eth = next((a for a in data_wallet['assets'] if a['ticker_id'] == 'ETH'), {})
        usdt = next((a for a in data_wallet['assets'] if a['ticker_id'] == 'USDT'), {})
        assert Decimal(eth['quantity']) == Decimal('-2.5')
        assert Decimal(usdt['quantity']) == Decimal('7500.0')

    async def test_create_transaction_portfolio_transfer(self, client, auth_headers, wallet, portfolio, portfolio_asset, transaction):
        portfolio_asset.quantity = Decimal('1.5')
        portfolio2_data = {'name': 'Портфель 2', 'market': 'crypto'}
        data_portfolio2 = (await client.post('/portfolios/', json=portfolio2_data, headers=auth_headers)).json()

        transfer_transaction = {
            'date': datetime.now(UTC).isoformat(),
            'ticker_id': 'BTC',
            'quantity': '0.75',  # Переводим 0.75 BTC
            'type': 'TransferOut',
            'portfolio_id': portfolio.id,
            'portfolio2_id': data_portfolio2['id'],
            'comment': 'Перевод части BTC',
        }

        response = await client.post('/transactions/', json=transfer_transaction, headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK

        # Проверяем оба портфеля
        data_portfolio1 = (await client.get(f'/portfolios/{portfolio.id}', headers=auth_headers)).json()
        data_portfolio2 = (await client.get(f'/portfolios/{data_portfolio2['id']}', headers=auth_headers)).json()

        # Ищем актив BTC в каждом портфеле
        btc_in_portfolio1 = next((a for a in data_portfolio1['assets'] if a['ticker_id'] == 'BTC'), {})
        btc_in_portfolio2 = next((a for a in data_portfolio2['assets'] if a['ticker_id'] == 'BTC'), {})

        assert Decimal(btc_in_portfolio1['quantity']) == Decimal('0.75')  # 1.5 - 0.75
        assert Decimal(btc_in_portfolio2['quantity']) == Decimal('0.75')  # пришло 0.75

    async def test_create_transaction_input_wallet(self, client, auth_headers, wallet):
        transaction_data = {
            'date': datetime.now(UTC).isoformat(),
            'ticker_id': 'USDT',
            'quantity': '10000.0',
            'type': 'Input',
            'wallet_id': wallet.id,
            'comment': 'Пополнение кошелька',
        }

        response = await client.post('/transactions/', json=transaction_data, headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK

        data_wallet = (await client.get(f'/wallets/{wallet.id}', headers=auth_headers)).json()

        assert len(data_wallet['assets']) == 1
        usdt = next((a for a in data_wallet['assets'] if a['ticker_id'] == 'USDT'), {})
        assert Decimal(usdt['quantity']) == Decimal('10000.0')

    async def test_create_transaction_output_wallet(self, client, auth_headers, wallet):
        # Сначала пополним кошелёк
        input_transaction_data = {
            'date': datetime.now(UTC).isoformat(),
            'ticker_id': 'USDT',
            'quantity': '10000.0',
            'type': 'Input',
            'wallet_id': wallet.id,
            'comment': 'Пополнение кошелька',
        }
        response = await client.post('/transactions/', json=input_transaction_data, headers=auth_headers)

        # Вывод части средств
        output_transaction_data = {
            'date': datetime.now(UTC).isoformat(),
            'ticker_id': 'USDT',
            'quantity': '3000.0',  # Выводим 3000 USDT
            'type': 'Output',
            'wallet_id': wallet.id,
            'comment': 'Вывод средств',
        }

        response = await client.post('/transactions/', json=output_transaction_data, headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK

        data_wallet = (await client.get(f'/wallets/{wallet.id}', headers=auth_headers)).json()

        usdt = next((a for a in data_wallet['assets'] if a['ticker_id'] == 'USDT'), {})
        assert Decimal(usdt['quantity']) == Decimal('7000.0')  # 10 - 3

    async def test_update_transaction(self, client, auth_headers, portfolio, wallet, transaction):
        update_data = {
            'date': datetime.now(UTC).isoformat(),
            'ticker_id': 'BTC',
            'ticker2_id': 'USDT',
            'quantity': '2.0',  # Изменяем количество
            'quantity2': '20000.0',
            'type': 'Buy',
            'portfolio_id': portfolio.id,
            'wallet_id': wallet.id,
        }

        response = await client.put(f'/transactions/{transaction.id}', json=update_data, headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data['success'] is True
        assert 'изменена' in data.get('message', '').lower()
        assert Decimal(data['transaction']['quantity']) == Decimal('2.0')

        # Проверяем что актив обновился
        data_portfolio = (await client.get(f'/portfolios/{portfolio.id}', headers=auth_headers)).json()
        assets = data_portfolio['assets']
        assert len(assets) == 2
        btc = next((a for a in data_portfolio['assets'] if a['ticker_id'] == 'BTC'), {})
        assert Decimal(btc['quantity']) == Decimal('0.5')

    async def test_delete_transaction(self, client, auth_headers, portfolio, wallet, transaction):
        response = await client.delete(f'/transactions/{transaction.id}', headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data['success'] is True
        assert 'удалена' in data.get('message', '').lower()

        # Проверяем что актив обнулился (транзакция отменена)
        data_portfolio = (await client.get(f'/portfolios/{portfolio.id}', headers=auth_headers)).json()
        assets = data_portfolio['assets']

        # Актив может остаться, но количество должно быть -1.5
        if len(assets) > 0:
            assert Decimal(assets[0]['quantity']) == Decimal('-1.5')

    async def test_create_transaction_invalid_type(self, client, auth_headers, portfolio):
        transaction_data = {
            'date': datetime.now(UTC).isoformat(),
            'ticker_id': 'AAPL',
            'quantity': '10.0',
            'type': 'InvalidType',  # Несуществующий тип
            'portfolio_id': portfolio.id,
        }

        response = await client.post('/transactions/', json=transaction_data, headers=auth_headers)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    async def test_create_transaction_missing_required_fields(self, client, auth_headers):
        transaction_data = {
            'date': datetime.now(UTC).isoformat(),
            'ticker_id': 'AAPL',
            'quantity': '10.0',
            # Нет type - обязательное поле
        }

        response = await client.post('/transactions/', json=transaction_data, headers=auth_headers)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
