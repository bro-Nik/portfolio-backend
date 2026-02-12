from itertools import product

from app.models import Transaction


class TransactionAnalyzer:
    @staticmethod
    def get_portfolio_ticker_pairs(t: Transaction) -> list[tuple[int, str]]:
        """Получить пары (portfolio_id, ticker_id) из транзакции."""
        return TransactionAnalyzer._combine_asset_identifiers(
            t.portfolio_id, t.portfolio2_id, t.ticker_id, t.ticker2_id,
        )

    @staticmethod
    def get_wallet_ticker_pairs(t: Transaction) -> list[tuple[int, str]]:
        """Получить пары (wallet_id, ticker_id) из транзакции."""
        return TransactionAnalyzer._combine_asset_identifiers(
            t.wallet_id, t.wallet2_id, t.ticker_id, t.ticker2_id,
        )

    @staticmethod
    def _combine_asset_identifiers(
        id1: int | None,
        id2: int | None,
        ticker1: str | None,
        ticker2: str | None,
    ) -> list[tuple[int, str]]:
        """Создать все возможные комбинации ID и тикеров."""
        ids = [id_ for id_ in (id1, id2) if id_]
        tickers = [ticker for ticker in (ticker1, ticker2) if ticker]

        unique_pairs = {(id_, ticker) for id_, ticker in product(ids, tickers)}
        return list(unique_pairs)


get_portfolio_pairs = TransactionAnalyzer.get_portfolio_ticker_pairs
get_wallet_pairs = TransactionAnalyzer.get_wallet_ticker_pairs
