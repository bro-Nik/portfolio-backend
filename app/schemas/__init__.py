from .portfolio_asset import (
    AssetResponse,
    AssetDetailResponse
)
from .portfolio import (
    PortfolioEdit,
    PortfolioResponse,
    PortfolioListResponse,
    PortfolioDeleteResponse
)

from .wallet import (
    WalletEdit,
    WalletListResponse,
    WalletResponse,
    WalletDeleteResponse,
)

from .transaction import (
    TransactionResponse,
    TransactionCreate,
    TransactionUpdate
)

from .ticker import TickerData

# Перестраиваем модели с форвард-декларациями
PortfolioResponse.model_rebuild()
PortfolioListResponse.model_rebuild()

__all__ = [
    "AssetResponse",
    "AssetDetailResponse", 
    "PortfolioEdit",
    "PortfolioResponse",
    "PortfolioListResponse", 
    "PortfolioDeleteResponse",
    "WalletEdit",
    "WalletListResponse",
    "WalletResponse",
    "WalletDeleteResponse",
    "TransactionResponse",
    "TransactionCreate",
    "TransactionUpdate",
    "TickerData"
]
