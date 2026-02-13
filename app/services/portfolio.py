import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models import Portfolio, Transaction
from app.repositories import PortfolioRepository
from app.schemas import (
    PortfolioAssetCreateRequest,
    PortfolioCreate,
    PortfolioCreateRequest,
    PortfolioDeleteResponse,
    PortfolioListResponse,
    PortfolioResponse,
    PortfolioUpdate,
    PortfolioUpdateRequest,
)
from app.services.portfolio_asset import PortfolioAssetService


class PortfolioService:
    """Сервис для работы с портфелями пользователей."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = PortfolioRepository(session)
        self.asset_service = PortfolioAssetService(session)

    async def get_many(self, user_id: int) -> PortfolioListResponse:
        """Получить все портфели пользователя."""
        portfolios = await self.repo.get_many_by_user(user_id, include_assets=True)
        return PortfolioListResponse(portfolios=portfolios)

    async def get(self, portfolio_id: int, user_id: int) -> PortfolioResponse:
        """Получить портфель пользователя."""
        portfolio = await self._get_or_raise(portfolio_id, user_id)
        await self.session.refresh(portfolio, ['assets'])
        return PortfolioResponse.model_validate(portfolio)

    async def create(self, user_id: int, data: PortfolioCreateRequest) -> PortfolioResponse:
        """Создать портфель для пользователя."""
        await self._validate_create_data(data, user_id)

        portfolio_to_db = PortfolioCreate(**data.model_dump(), user_id=user_id)
        portfolio = await self.repo.create(portfolio_to_db)
        await self.session.flush()

        await self.session.refresh(portfolio, ['assets'])
        return portfolio

    async def update(self, portfolio_id: int, user_id: int, data: PortfolioUpdateRequest) -> PortfolioResponse:
        """Обновить портфель пользователя."""
        portfolio = await self._get_or_raise(portfolio_id, user_id)
        await self._validate_update_data(data, user_id, portfolio)

        portfolio_to_db = PortfolioUpdate(**data.model_dump())
        portfolio = await self.repo.update(portfolio_id, portfolio_to_db)

        await self.session.refresh(portfolio, ['assets'])
        return portfolio

    async def delete(self, portfolio_id: int, user_id: int) -> PortfolioDeleteResponse:
        """Удалить портфель пользователя."""
        await self._get_or_raise(portfolio_id, user_id)
        await self.repo.delete(portfolio_id)
        return PortfolioDeleteResponse(portfolio_id=portfolio_id)

    async def add_asset(self, portfolio_id: int, user_id: int, data: PortfolioAssetCreateRequest) -> PortfolioResponse:
        """Добавить актив в портфель пользователя."""
        await self.asset_service.create(data)
        return await self.get(portfolio_id, user_id)

    async def delete_asset(self, portfolio_id: int, user_id: int, asset_id: int) -> PortfolioResponse:
        """Удалить актив из портфеля пользователя."""
        await self.asset_service.delete(asset_id)
        return await self.get(portfolio_id, user_id)

    async def handle_transaction(self, user_id: int, t: Transaction, *, cancel: bool = False) -> None:
        """Обработка транзакции."""
        if not t.portfolio_id:
            return

        if t.type in ('Buy', 'Sell'):
            await self._handle_trade(user_id, t)
        elif t.type == 'Earning':
            await self._handle_earning(user_id, t)
        elif t.type in ('TransferIn', 'TransferOut'):
            await self._handle_transfer(user_id, t)
        elif t.type in ('Input', 'Output'):
            await self._handle_input_output(user_id, t)

        # Уведомление сервиса актива о новой транзакции
        await self.asset_service.handle_transaction(t, cancel=cancel)

    async def _get_or_raise(self, portfolio_id: int, user_id: int) -> Portfolio:
        portfolio = await self.repo.get_by_id_and_user(portfolio_id, user_id)
        if not portfolio:
            raise NotFoundError(f'Портфель id={portfolio_id} не найден')
        return portfolio

    async def _validate_create_data(self, data: PortfolioCreateRequest, user_id: int) -> None:
        await self._validate_unique_name(data.name, user_id)

    async def _validate_update_data(self, data: PortfolioUpdateRequest, user_id: int, portfolio: Portfolio) -> None:
        if data.name != portfolio.name:
            await self._validate_unique_name(data.name, user_id)

    async def _validate_unique_name(self, name: str, user_id: int) -> None:
        if await self.repo.exists_by_name_and_user(name, user_id):
            raise ConflictError('Портфель с таким именем уже существует')

    async def _validate_portfolios(self, user_id: int, *portfolio_ids: int | None) -> None:
        if ids := [id_ for id_ in portfolio_ids if id_ is not None]:
            await asyncio.gather(*[self._get_or_raise(id_, user_id) for id_ in ids])

    async def _handle_trade(self, user_id: int, t: Transaction) -> None:
        await self._validate_portfolios(user_id, t.portfolio_id)

    async def _handle_earning(self, user_id: int, t: Transaction) -> None:
        await self._validate_portfolios(user_id, t.portfolio_id)

    async def _handle_transfer(self, user_id: int, t: Transaction) -> None:
        await self._validate_portfolios(user_id, t.portfolio_id, t.portfolio2_id)

    async def _handle_input_output(self, user_id: int, t: Transaction) -> None:
        await self._validate_portfolios(user_id, t.portfolio_id)
