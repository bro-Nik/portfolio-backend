from fastapi import status

from app.models import Wallet


class TestWalletsAPI:
    async def test_get_wallets_empty(self, client, auth_headers):
        response = await client.get('/wallets/', headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert 'wallets' in data
        assert len(data['wallets']) == 0

    async def test_get_wallets(self, client, auth_headers, wallet):
        response = await client.get('/wallets/', headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert 'wallets' in data
        assert len(data['wallets']) == 1
        data_wallet = data['wallets'][0]
        assert data_wallet['id'] == wallet.id
        assert data_wallet['name'] == wallet.name
        assert data_wallet['comment'] == wallet.comment

    async def test_get_wallet_success(self, client, auth_headers, wallet):
        response = await client.get(f'/wallets/{wallet.id}', headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['id'] == wallet.id
        assert data['name'] == wallet.name
        assert data['comment'] == wallet.comment

    async def test_get_wallet_not_found(self, client, auth_headers):
        response = await client.get('/wallets/99999', headers=auth_headers)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert 'не найден' in data.get('detail', '').lower()

    async def test_create_wallet_success(self, client, auth_headers, db_session):
        wallet_data = {'name': 'Мой кошелек', 'comment': 'Комментарий'}

        response = await client.post('/wallets/', json=wallet_data, headers=auth_headers)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data['name'] == wallet_data['name']
        assert data['comment'] == wallet_data['comment']
        assert 'id' in data
        assert 'assets' in data
        assert len(data['assets']) == 0

        # Проверяем, что кошелек создан в БД
        db_wallet = await db_session.get(Wallet, data['id'])
        assert db_wallet.name == wallet_data['name']

    async def test_create_wallet_duplicate_name(self, client, auth_headers, wallet):
        wallet_data = {'name': 'Тестовый кошелек'}

        response = await client.post('/wallets/', json=wallet_data, headers=auth_headers)

        assert response.status_code == status.HTTP_409_CONFLICT
        data = response.json()
        assert 'уже существует' in data.get('detail', '').lower()

    async def test_create_wallet_missing_required_fields(self, client, auth_headers):
        wallet_data = {'comment': 'Неполный кошелек'}  # Нет name - обязательное поле

        response = await client.post('/wallets/', json=wallet_data, headers=auth_headers)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
        data = response.json()
        assert 'detail' in data

    async def test_update_wallet_success(self, client, auth_headers, wallet, db_session):
        update_data = {'name': 'Новое имя', 'comment': 'Обновленный комментарий'}

        response = await client.put(f'/wallets/{wallet.id}', json=update_data, headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['name'] == update_data['name']
        assert data['comment'] == update_data['comment']

        # Проверяем, что кошелек изменен в БД
        db_wallet = await db_session.get(Wallet, data['id'])
        assert db_wallet.name == update_data['name']

    async def test_delete_wallet_success(self, client, auth_headers, wallet, db_session):
        response = await client.delete(f'/wallets/{wallet.id}', headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['wallet_id'] == wallet.id

        # Проверяем, что кошелек удален в БД
        db_wallet = await db_session.get(Wallet, data['wallet_id'])
        assert db_wallet is None

    async def test_get_asset_transactions(self, client, auth_headers, wallet_asset, transaction):
        response = await client.get(f'/wallets/assets/{wallet_asset.id}/transactions', headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert data[0]['ticker_id'] == 'BTC'

    async def test_get_asset_distribution(self, client, auth_headers, wallet_asset, wallet):
        response = await client.get(f'/wallets/assets/{wallet_asset.id}/distribution', headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert 'total_quantity_all_wallets' in data
        assert 'wallets' in data

    async def test_unauthenticated_access(self, client):
        response = await client.get('/wallets/')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
