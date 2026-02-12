from itertools import product

from app.models import Transaction


class TransactionAnalyzer:
    @staticmethod
    def _get_affected_assets(
        id1: int | None,
        id2: int | None,
        ticker1: str | None,
        ticker2: str | None,
    ) -> list[tuple[int, str]]:
        """Получить все комбинации ID и тикеров."""
        ids = [id_ for id_ in (id1, id2) if id_]
        tickers = [ticker for ticker in (ticker1, ticker2) if ticker]

        unique_pairs = {(id_, ticker) for id_, ticker in product(ids, tickers)}
        return list(unique_pairs)

    @staticmethod
    def get_affected_portfolio_assets(t: Transaction) -> list[tuple[int, str]]:
        """Получить список затронутых активов портфелей (portfolio_id, ticker_id)."""
        return TransactionAnalyzer._get_affected_assets(
            t.portfolio_id, t.portfolio2_id, t.ticker_id, t.ticker2_id,
        )

    @staticmethod
    def get_affected_wallet_assets(t: Transaction) -> list[tuple[int, str]]:
        """Получить список затронутых активов кошельков (wallet_id, ticker_id)."""
        return TransactionAnalyzer._get_affected_assets(
            t.wallet_id, t.wallet2_id, t.ticker_id, t.ticker2_id,
        )
