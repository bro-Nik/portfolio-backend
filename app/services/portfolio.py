import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models import Portfolio, Transaction
from app.repositories import PortfolioRepository
from app.schemas import (
    PortfolioCreate,
    PortfolioCreateRequest,
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

    async def get_portfolios(self, user_id: int) -> list[PortfolioResponse]:
        """Получить все портфели пользователя."""
        portfolios = await self.repo.get_many_by_user(user_id, include_assets=True)
        return [PortfolioResponse.model_validate(p) for p in portfolios]

    async def get_portfolio(self, portfolio_id: int, user_id: int) -> PortfolioResponse:
        """Получить портфель пользователя."""
        portfolio = await self._get_portfolio_or_raise(portfolio_id, user_id)
        await self.session.refresh(portfolio, ['assets'])
        return PortfolioResponse.model_validate(portfolio)

    async def create_portfolio(
        self,
        user_id: int,
        portfolio_data: PortfolioCreateRequest,
    ) -> PortfolioResponse:
        """Создать портфель для пользователя."""
        await self._validate_create_data(portfolio_data, user_id)

        portfolio_to_db = PortfolioCreate(
            **portfolio_data.model_dump(),
            user_id=user_id,
        )

        portfolio = await self.repo.create(portfolio_to_db)
        await self.session.flush()
        await self.session.refresh(portfolio, ['assets'])
        return portfolio

    async def update_portfolio(
        self,
        portfolio_id: int,
        user_id: int,
        portfolio_data: PortfolioUpdateRequest,
    ) -> PortfolioResponse:
        """Обновить портфель пользователя."""
        portfolio = await self._get_portfolio_or_raise(portfolio_id, user_id)
        await self._validate_update_data(portfolio_data, user_id, portfolio)

        portfolio_to_db = PortfolioUpdate(**portfolio_data.model_dump())

        portfolio = await self.repo.update(portfolio_id, portfolio_to_db)
        await self.session.refresh(portfolio, ['assets'])
        return portfolio

    async def delete_portfolio(self, portfolio_id: int, user_id: int) -> None:
        """Удалить портфель пользователя."""
        await self._get_portfolio_or_raise(portfolio_id, user_id)
        await self.repo.delete(portfolio_id)

    async def handle_transaction(
        self,
        user_id: int,
        t: Transaction,
        *,
        cancel: bool = False,
    ) -> None:
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

    async def _get_portfolio_or_raise(self, portfolio_id: int, user_id: int) -> Portfolio:
        """Получить портфель пользователя."""
        portfolio = await self.repo.get_by_id_and_user(portfolio_id, user_id)
        if not portfolio:
            raise NotFoundError(f'Портфель id={portfolio_id} не найден')
        return portfolio

    async def _validate_create_data(self, data: PortfolioCreateRequest, user_id: int) -> None:
        """Валидация данных для создания портфеля."""
        await self._validate_unique_name(data.name, user_id)

    async def _validate_update_data(
        self,
        data: PortfolioUpdateRequest,
        user_id: int,
        portfolio: Portfolio,
    ) -> None:
        """Валидация данных для обновления портфеля."""
        if data.name != portfolio.name:
            await self._validate_unique_name(data.name, user_id)

    async def _validate_unique_name(self, name: str, user_id: int) -> None:
        if await self.repo.exists_by_name_and_user(name, user_id):
            raise ConflictError('Портфель с таким именем уже существует')

    async def _validate_portfolios(self, user_id: int, *portfolio_ids: int | None) -> None:
        if ids := [id_ for id_ in portfolio_ids if id_ is not None]:
            tasks = [self._get_portfolio_or_raise(id_, user_id) for id_ in ids]
            await asyncio.gather(*tasks)

    async def _handle_trade(self, user_id: int, t: Transaction) -> None:
        """Обработка торговой операции."""
        await self._validate_portfolios(user_id, t.portfolio_id)

    async def _handle_earning(self, user_id: int, t: Transaction) -> None:
        """Обработка заработка."""
        await self._validate_portfolios(user_id, t.portfolio_id)

    async def _handle_transfer(self, user_id: int, t: Transaction) -> None:
        """Обработка перевода между портфелями."""
        await self._validate_portfolios(user_id, t.portfolio_id, t.portfolio2_id)

    async def _handle_input_output(self, user_id: int, t: Transaction) -> None:
        """Обработка ввода-вывода."""
        await self._validate_portfolios(user_id, t.portfolio_id)
