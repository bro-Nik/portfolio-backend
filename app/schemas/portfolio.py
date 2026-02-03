from pydantic import BaseModel, ConfigDict


class PortfolioBase(BaseModel):
    """Базовые поля."""

    name: str
    comment: str | None = None


class PortfolioCreateRequest(PortfolioBase):
    """Создание нового портфеля."""

    market: str


class PortfolioUpdateRequest(PortfolioBase):
    """Обновление портфеля."""


class PortfolioCreate(PortfolioBase):
    """Создание портфеля в БД."""

    user_id: int
    market: str


class PortfolioUpdate(PortfolioBase):
    """Обновление портфеля в БД."""


class PortfolioResponse(PortfolioBase):
    """Ответ с данными портфеля."""

    id: int
    market: str
    assets: list['PortfolioAssetResponse'] = []

    model_config = ConfigDict(from_attributes=True)


class PortfolioListResponse(BaseModel):
    """Ответ со списком портфелей."""

    portfolios: list[PortfolioResponse]


class PortfolioDeleteResponse(BaseModel):
    """Ответ после удаления портфелея."""

    portfolio_id: int
