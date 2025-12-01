from typing import List
from pydantic import BaseModel


class WalletAssetDetailResponse(BaseModel):
    transactions: List[dict]
    distribution: dict
