import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models import Transaction, Wallet
from app.repositories import WalletRepository
from app.schemas import (
    WalletCreate,
    WalletCreateRequest,
    WalletDeleteResponse,
    WalletListResponse,
    WalletResponse,
    WalletUpdate,
    WalletUpdateRequest,
)
from app.services.wallet_asset import WalletAssetService


class WalletService:
    """Сервис для работы с кошельками пользователей."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = WalletRepository(session)
        self.asset_service = WalletAssetService(session)

    async def get_many(self, user_id: int) -> WalletListResponse:
        """Получить все кошельки пользователя."""
        wallets = await self.repo.get_many_by_user(user_id, include_assets=True)
        return WalletListResponse(wallets=wallets)

    async def get(self, wallet_id: int, user_id: int) -> WalletResponse:
        """Получить кошелек пользователя."""
        wallet = await self._get_or_raise(wallet_id, user_id)
        await self.session.refresh(wallet, ['assets'])
        return WalletResponse.model_validate(wallet)

    async def create(self, user_id: int, data: WalletCreateRequest) -> WalletResponse:
        """Создать кошелек для пользователя."""
        await self._validate_create_data(data, user_id)

        wallet_to_db = WalletCreate(**data.model_dump(), user_id=user_id)
        wallet = await self.repo.create(wallet_to_db)
        await self.session.flush()

        await self.session.refresh(wallet, ['assets'])
        return wallet

    async def update(self, wallet_id: int, user_id: int, data: WalletUpdateRequest) -> WalletResponse:
        """Обновить кошелек пользователя."""
        wallet = await self._get_or_raise(wallet_id, user_id)
        await self._validate_update_data(data, user_id, wallet)

        wallet_to_db = WalletUpdate(**data.model_dump())
        wallet = await self.repo.update(wallet_id, wallet_to_db)

        await self.session.refresh(wallet, ['assets'])
        return wallet

    async def delete(self, wallet_id: int, user_id: int) -> WalletDeleteResponse:
        """Удалить кошелек пользователя."""
        await self._get_or_raise(wallet_id, user_id)
        await self.repo.delete(wallet_id)
        return WalletDeleteResponse(wallet_id=wallet_id)

    async def handle_transaction(self, user_id: int, t: Transaction, *, cancel: bool = False) -> None:
        """Обработка транзакции."""
        if not t.wallet_id:
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

    async def _get_or_raise(self, wallet_id: int, user_id: int) -> Wallet:
        wallet = await self.repo.get_by_id_and_user(wallet_id, user_id)
        if not wallet:
            raise NotFoundError(f'Кошелек id={wallet_id} не найден')
        return wallet

    async def _validate_create_data(self, data: WalletCreateRequest, user_id: int) -> None:
        await self._validate_unique_name(data.name, user_id)

    async def _validate_update_data(self, data: WalletUpdateRequest, user_id: int, wallet: Wallet) -> None:
        if data.name != wallet.name:
            await self._validate_unique_name(data.name, user_id)

    async def _validate_unique_name(self, name: str, user_id: int) -> None:
        if await self.repo.exists_by_name_and_user(name, user_id):
            raise ConflictError('Кошелек с таким именем уже существует')

    async def _validate_wallets(self, user_id: int, *wallet_ids: int | None) -> None:
        if ids := [id_ for id_ in wallet_ids if id_ is not None]:
            await asyncio.gather(*[self._get_or_raise(id_, user_id) for id_ in ids])

    async def _handle_trade(self, user_id: int, t: Transaction) -> None:
        await self._validate_wallets(user_id, t.wallet_id)

    async def _handle_earning(self, user_id: int, t: Transaction) -> None:
        await self._validate_wallets(user_id, t.wallet_id)

    async def _handle_transfer(self, user_id: int, t: Transaction) -> None:
        await self._validate_wallets(user_id, t.wallet_id, t.wallet2_id)

    async def _handle_input_output(self, user_id: int, t: Transaction) -> None:
        await self._validate_wallets(user_id, t.wallet_id)
