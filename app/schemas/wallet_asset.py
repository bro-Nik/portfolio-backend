from typing import List
from pydantic import BaseModel


class WalletAssetResponse(BaseModel):
    transactions: List[dict]
    distribution: dict
