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

from .wallet_asset import (
    WalletAssetDetailResponse,
)

from .wallet import (
    WalletEdit,
    WalletListResponse,
    WalletResponse,
    WalletDeleteResponse,
    WalletAssetResponse,
)

from .transaction import (
    TransactionResponse,
    TransactionCreate,
    TransactionUpdate,
    TransactionResponseWithAssets,
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
    "WalletAssetDetailResponse",
    "WalletEdit",
    "WalletListResponse",
    "WalletResponse",
    "WalletDeleteResponse",
    "WalletAssetResponse",
    "TransactionResponse",
    "TransactionCreate",
    "TransactionUpdate",
    "TickerData",
    "TransactionResponseWithAssets",
]
