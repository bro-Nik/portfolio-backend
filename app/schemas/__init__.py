from .common import ErrorResponse
from .portfolio_asset import (
    PortfolioAssetCreate,
    PortfolioAssetCreateRequest,
    PortfolioAssetResponse,
    PortfolioAssetUpdate,
)
from .portfolio import (
    PortfolioCreate,
    PortfolioDeleteResponse,
    PortfolioListResponse,
    PortfolioResponse,
    PortfolioUpdate,
    PortfolioCreateRequest,
    PortfolioUpdateRequest,
)
from .wallet_asset import (
    WalletAssetCreate,
    WalletAssetResponse,
    WalletAssetUpdate,
)
from .wallet import (
    WalletCreate,
    WalletCreateRequest,
    WalletDeleteResponse,
    WalletListResponse,
    WalletResponse,
    WalletUpdate,
    WalletUpdateRequest,
)
from .transaction import (
    TransactionCreateRequest,
    TransactionResponse,
    TransactionResponseWithAssets,
    TransactionUpdateRequest,
    TransactionUpdate,
    TransactionCreate,
)

# Перестраиваем модели с форвард-декларациями
PortfolioResponse.model_rebuild()
PortfolioListResponse.model_rebuild()
WalletResponse.model_rebuild()
TransactionResponseWithAssets.model_rebuild()
