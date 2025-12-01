from typing import List
from app.models import Transaction


class TransactionAnalyzer:
    @staticmethod
    def get_affected_portfolio_assets(t: Transaction) -> List[tuple[int, str]]:
        """Получить список затронутых активов портфелей (portfolio_id, ticker_id)"""
        affected_assets = set()

        if t.portfolio_id and t.ticker_id:
            affected_assets.add((t.portfolio_id, t.ticker_id))

        if t.portfolio_id and t.ticker2_id:
            affected_assets.add((t.portfolio_id, t.ticker2_id))

        if t.portfolio2_id and t.ticker_id:
            affected_assets.add((t.portfolio2_id, t.ticker_id))

        if t.portfolio2_id and t.ticker2_id:
            affected_assets.add((t.portfolio2_id, t.ticker2_id))

        return list(affected_assets)

    @staticmethod
    def get_affected_wallet_assets(t: Transaction) -> List[tuple[int, str]]:
        """Получить список затронутых активов кошельков (wallet_id, ticker_id)"""
        affected_assets = set()

        if t.wallet_id and t.ticker_id:
            affected_assets.add((t.wallet_id, t.ticker_id))

        if t.wallet_id and t.ticker2_id:
            affected_assets.add((t.wallet_id, t.ticker2_id))

        if t.wallet2_id and t.ticker_id:
            affected_assets.add((t.wallet2_id, t.ticker_id))

        if t.wallet2_id and t.ticker2_id:
            affected_assets.add((t.wallet2_id, t.ticker2_id))

        return list(affected_assets)
