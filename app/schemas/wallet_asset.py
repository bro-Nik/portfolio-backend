from typing import List
from pydantic import BaseModel


class WalletAssetEdit(BaseModel):
    pass


class WalletAssetDetailResponse(BaseModel):
    transactions: List[dict]
    distribution: dict
