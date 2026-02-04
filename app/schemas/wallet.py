from pydantic import BaseModel, ConfigDict


class WalletBase(BaseModel):
    """Базовые поля."""

    name: str
    comment: str | None = None


class WalletCreateRequest(WalletBase):
    """Создание нового кошелька."""


class WalletUpdateRequest(WalletBase):
    """Обновление кошелька."""


class WalletCreate(WalletBase):
    """Создание кошелька в БД."""

    user_id: int


class WalletUpdate(WalletBase):
    """Обновление кошелька в БД."""


class WalletResponse(WalletBase):
    """Ответ с данными кошелька."""

    id: int
    assets: list['WalletAssetResponse'] = []

    model_config = ConfigDict(from_attributes=True)


class WalletListResponse(BaseModel):
    """Ответ со списком кошельков."""

    wallets: list[WalletResponse]


class WalletDeleteResponse(BaseModel):
    """Ответ после удаления кошелька."""

    wallet_id: int
