from fastapi import status

from app.models import PortfolioAsset, Portfolio


class TestPortfoliosAPI:
    async def test_get_portfolios_empty(self, client, auth_headers):
        response = await client.get('/portfolios/', headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert 'portfolios' in data
        assert len(data['portfolios']) == 0

    async def test_get_portfolios(self, client, auth_headers, portfolio):
        response = await client.get('/portfolios/', headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert 'portfolios' in data
        assert len(data['portfolios']) == 1

        data_portfolio = data['portfolios'][0]
        assert data_portfolio['id'] == portfolio.id
        assert data_portfolio['name'] == portfolio.name
        assert data_portfolio['market'] == portfolio.market
        assert data_portfolio['comment'] == portfolio.comment

    async def test_get_portfolio_success(self, client, auth_headers, portfolio):
        response = await client.get(f'/portfolios/{portfolio.id}', headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['id'] == portfolio.id
        assert data['name'] == portfolio.name
        assert data['market'] == portfolio.market

    async def test_get_portfolio_not_found(self, client, auth_headers):
        response = await client.get('/portfolios/99999', headers=auth_headers)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert 'не найден' in data.get('detail', '').lower()

    async def test_create_portfolio_success(self, client, auth_headers, db_session):
        portfolio_data = {'name': 'Мой портфель', 'market': 'stock', 'comment': 'Комментарий'}

        response = await client.post('/portfolios/', json=portfolio_data, headers=auth_headers)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data['name'] == portfolio_data['name']
        assert data['market'] == portfolio_data['market']
        assert data['comment'] == portfolio_data['comment']
        assert 'id' in data
        assert 'assets' in data
        assert len(data['assets']) == 0

        # Проверяем, что портфель создан в БД
        db_portfolio = await db_session.get(Portfolio, data['id'])
        assert db_portfolio.name == portfolio_data['name']

    async def test_create_portfolio_duplicate_name(self, client, auth_headers, portfolio):
        portfolio_data = {'name': 'Тестовый портфель', 'market': 'stock'}

        response = await client.post('/portfolios/', json=portfolio_data, headers=auth_headers)

        assert response.status_code == status.HTTP_409_CONFLICT
        data = response.json()
        assert 'уже существует' in data.get('detail', '').lower()

    async def test_create_portfolio_missing_required_fields(self, client, auth_headers):
        portfolio_data = {'name': 'Неполный портфель'}  # Нет market - обязательное поле

        response = await client.post('/portfolios/', json=portfolio_data, headers=auth_headers)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
        data = response.json()
        assert 'detail' in data

    async def test_update_portfolio_success(self, client, auth_headers, portfolio, db_session):
        update_data = {'name': 'Новое имя', 'comment': 'Обновленный комментарий'}

        response = await client.put(f'/portfolios/{portfolio.id}', json=update_data, headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['name'] == update_data['name']
        assert data['comment'] == update_data['comment']
        assert data['market'] == portfolio.market  # Не изменилось

        # Проверяем, что портфель изменен в БД
        db_portfolio = await db_session.get(Portfolio, data['id'])
        assert db_portfolio.name == update_data['name']

    async def test_delete_portfolio_success(self, client, auth_headers, portfolio, db_session):
        response = await client.delete(f'/portfolios/{portfolio.id}', headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['portfolio_id'] == portfolio.id

        # Проверяем, что портфель удален в БД
        db_portfolio = await db_session.get(Portfolio, data['portfolio_id'])
        assert db_portfolio is None

    async def test_add_asset_to_portfolio(self, client, auth_headers, portfolio, db_session):
        asset_data = {'ticker_id': 'BTC', 'portfolio_id': portfolio.id}

        response = await client.post(f'/portfolios/{portfolio.id}/assets', json=asset_data, headers=auth_headers)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert len(data['assets']) == 1
        asset = data['assets'][0]
        assert asset['ticker_id'] == 'BTC'

        # Проверяем, что актив создан в БД
        asset = await db_session.get(PortfolioAsset, asset['id'])
        assert asset is not None
        assert asset.ticker_id == asset_data['ticker_id']

    async def test_get_asset_detail(self, client, auth_headers, portfolio, portfolio_asset, transaction):
        response = await client.get(f'/portfolios/assets/{portfolio_asset.id}', headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert 'transactions' in data
        assert 'distribution' in data
        assert len(data['transactions']) > 0
        assert data['transactions'][0]['ticker_id'] == 'BTC'

    async def test_unauthenticated_access(self, client):
        response = await client.get('/portfolios/')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
