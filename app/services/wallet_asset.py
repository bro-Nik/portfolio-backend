from sqlalchemy.ext.asyncio import AsyncSession

from app.models import WalletAsset, Transaction
from app.repositories.wallet_asset import WalletAssetRepository


class WalletAssetService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = WalletAssetRepository()

    async def get_or_create(self, ticker_id: str, wallet_id: int) -> WalletAsset:
        asset = await self.repo.get(self.db, ticker_id, wallet_id)

        if not asset:
            asset = await self._create(ticker_id, wallet_id)
        return asset

    async def _create(self, ticker_id: str, wallet_id: int) -> WalletAsset:
        new_asset = WalletAsset(ticker_id=ticker_id, wallet_id=wallet_id)
        asset = await self.repo.create(self.db, new_asset)
        return asset

    async def get_asset_detail(self, asset_id: int, user_id: int) -> dict:
        """Получение детальной информации об активе"""
        # Загружаем актив с тикером и кошельком
        asset = await self.repo.get_asset_with_details(self.db, asset_id, user_id)

        if not asset:
            raise ValueError("Актив не найден")

        # Подготовка транзакций
        asset_transactions = []
        for transaction in asset.transactions:
            asset_transactions.append({
                "id": transaction.id,
                "order": transaction.order,
                "portfolio_id": transaction.portfolio_id,
                "portfolio2_id": transaction.portfolio2_id,
                "wallet_id": transaction.wallet_id,
                "wallet2_id": transaction.wallet2_id,
                "date": transaction.date,
                "ticker_id": transaction.ticker_id,
                "ticker2_id": transaction.ticker2_id,
                "quantity": transaction.quantity,
                "quantity2": transaction.quantity2,
                "price": transaction.price,
                "price_usd": transaction.price_usd,
                "type": transaction.type,
                "comment": transaction.comment,
            })

        # Расчет распределения по кошелькам
        wallet_distribution = await self._calculate_wallet_distribution(
            asset.ticker_id, user_id
        )

        return {
            "transactions": asset_transactions,
            "distribution": wallet_distribution
        }

    async def _calculate_wallet_distribution(self, ticker_id: str, user_id: int) -> dict:
        """Расчет распределения актива по портфелям"""
        assets = await self.repo.get_by_ticker_and_user(self.db, ticker_id, user_id)

        total_quantity = sum(asset.quantity for asset in assets)

        wallet_distribution = []
        for asset in assets:
            percentage = (asset.quantity / total_quantity * 100) if total_quantity > 0 else 0
            wallet_distribution.append({
                "wallet_id": asset.wallet.id,
                "wallet_name": asset.wallet.name,
                "quantity": asset.quantity,
                "percentage_of_total": percentage
            })

        return {
            "total_quantity_all_wallets": total_quantity,
            "wallets": wallet_distribution
        }

    async def handle_transaction(self, t: Transaction, cancel = False):
        """Обработка транзакции"""
        direction = t.get_direction(cancel)

        if t.type in ('Buy', 'Sell'):
            await self._handle_trade(t, direction)
        elif t.type == 'Earning':
            await self._handle_earning(t, direction)
        elif t.type in ('TransferIn', 'TransferOut'):
            await self._handle_transfer(t, direction)
        elif t.type in ('Input', 'Output'):
            await self._handle_input_output(t, direction)

    async def _handle_trade(self, t: Transaction, direction: int):
        """Обработка торговой операции"""
        # Получение или создание активов
        asset1 = await self.get_or_create(t.ticker_id, t.wallet_id)
        asset2 = await self.get_or_create(t.ticker2_id, t.wallet_id)

        if t.order:
            self._handle_trade_order(asset1, t, direction, True)
            self._handle_trade_order(asset2, t, direction, False)
        else:
            self._handle_trade_execution(asset1, t, direction, True)
            self._handle_trade_execution(asset2, t, direction, False)

    def _handle_trade_execution(self, asset: WalletAsset, t: Transaction,
                                direction: int, is_primary: bool):
        """Обработка исполненной сделки"""
        if is_primary:
            # Базовый актив
            asset.quantity += t.quantity * direction
        else:
            # Котируемый актив (валюта расчета)
            asset.quantity -= t.quantity2 * direction

    def _handle_trade_order(self, asset: WalletAsset, t: Transaction,
                            direction: int, is_primary: bool):
        """Обработка ордера"""
        if is_primary:
            # Базовый актив
            if t.type == 'Buy':
                asset.buy_orders += t.quantity * t.price_usd * direction
            elif t.type == 'Sell':
                asset.sell_orders -= t.quantity * direction
        else:
            # Котируемый актив (валюта расчета)
            if t.type == 'Buy':
                asset.sell_orders -= t.quantity2 * direction

    async def _handle_earning(self, t: Transaction, direction: int):
        """Обработка заработка"""
        # Получение или создание актива
        asset = await self.get_or_create(t.ticker_id, t.wallet_id)
        asset.quantity += t.quantity * direction

    async def _handle_transfer(self, t: Transaction, direction: int):
        """Обработка перевода между портфелями"""
        if not (t.wallet_id and t.wallet2_id):
            return

        # Получение или создание активов
        asset1 = await self.get_or_create(t.ticker_id, t.wallet_id)
        asset2 = await self.get_or_create(t.ticker_id, t.wallet2_id)

        asset1.quantity -= t.quantity * direction
        asset2.quantity += t.quantity * direction

    async def _handle_input_output(self, t: Transaction, direction: int):
        """Обработка ввода-вывода"""
        # Получение или создание актива
        asset = await self.get_or_create(t.ticker_id, t.wallet_id)

        asset.quantity += t.quantity * direction
