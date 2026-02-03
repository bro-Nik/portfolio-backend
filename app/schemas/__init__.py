from .common import ErrorResponse
from .portfolio_asset import (
    PortfolioAssetCreate,
    PortfolioAssetCreateRequest,
    PortfolioAssetDetailResponse,
    PortfolioAssetResponse,
    PortfolioAssetUpdate,
)
from .portfolio import (
    PortfolioCreate,
    PortfolioDeleteResponse,
    PortfolioListResponse,
    PortfolioResponse,
    PortfolioUpdate,
)
from .wallet_asset import (
    WalletAssetCreate,
    WalletAssetDetailResponse,
    WalletAssetResponse,
    WalletAssetUpdate,
)
from .wallet import (
    WalletCreate,
    WalletCreateRequest,
    WalletDeleteResponse,
    WalletListResponse,
    WalletResponse,
    WalletToBuyResponse,
    WalletToSellResponse,
    WalletUpdate,
    WalletUpdateRequest,
)
from .transaction import (
    TransactionCreateRequest,
    TransactionResponse,
    TransactionResponseWithAssets,
    TransactionUpdateRequest,
    TransactionUpdate,
)

# Перестраиваем модели с форвард-декларациями
PortfolioResponse.model_rebuild()
PortfolioListResponse.model_rebuild()
WalletResponse.model_rebuild()
TransactionResponseWithAssets.model_rebuild()
