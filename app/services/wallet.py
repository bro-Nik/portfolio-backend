import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, NotFoundError
from app.models import Transaction, Wallet
from app.repositories import WalletRepository
from app.schemas import (
    WalletCreate,
    WalletCreateRequest,
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

    async def get_wallets(self, user_id: int) -> list[WalletResponse]:
        """Получить все кошельки пользователя."""
        wallets = await self.repo.get_many_by_user(user_id, include_assets=True)
        return [WalletResponse.model_validate(w) for w in wallets]

    async def get_wallet(self, wallet_id: int, user_id: int) -> WalletResponse:
        """Получить кошельк пользователя."""
        wallet = await self.repo.get_by_id_and_user_with_assets(wallet_id, user_id)

        if not wallet:
            raise NotFoundError(f'Кошелек id={wallet_id} не найден')

        return WalletResponse.model_validate(wallet)

    async def create_wallet(self, user_id: int, wallet_data: WalletCreateRequest) -> WalletResponse:
        """Создать кошельк для пользователя."""
        await self._validate_create_data(wallet_data, user_id)

        wallet_to_db = WalletCreate(
            **wallet_data.model_dump(),
            user_id=user_id,
        )

        wallet = await self.repo.create(wallet_to_db)
        await self.session.flush()
        return await self.get_wallet(wallet.id, user_id)  # Кошелек с активами

    async def update_wallet(
        self,
        wallet_id: int,
        user_id: int,
        wallet_data: WalletUpdateRequest,
    ) -> WalletResponse:
        """Обновить кошельк пользователя."""
        wallet = await self.get_wallet(wallet_id, user_id)
        await self._validate_update_data(wallet_data, user_id, wallet)

        wallet_to_db = WalletUpdate(**wallet_data.model_dump())

        wallet = await self.repo.update(wallet_id, wallet_to_db)
        return await self.get_wallet(wallet_id, user_id)  # Кошелек с активами

    async def delete_wallet(self, wallet_id: int, user_id: int) -> None:
        """Удалить кошельк пользователя."""
        await self.get_wallet(wallet_id, user_id)
        await self.repo.delete(wallet_id)

    async def handle_transaction(
        self,
        user_id: int,
        t: Transaction,
        *,
        cancel: bool = False,
    ) -> None:
        """Обработка транзакции."""
        if t.type in ('Buy', 'Sell'):
            await self._handle_trade(user_id, t)
        elif t.type == 'Earning':
            await self._handle_earning(user_id, t)
        elif t.type in ('TransferIn', 'TransferOut'):
            # Портфельный перевод
            if not (t.wallet_id and t.wallet2_id):
                return

            await self._handle_transfer(user_id, t)
        elif t.type in ('Input', 'Output'):
            await self._handle_input_output(user_id, t)

        # Уведомление сервиса актива о новой транзакции
        await self.asset_service.handle_transaction(t, cancel=cancel)

    async def _handle_trade(self, user_id: int, t: Transaction) -> None:
        """Обработка торговой операции."""
        # Валидация кошелька
        await self.get_wallet(t.wallet_id, user_id)

    async def _handle_earning(self, user_id: int, t: Transaction) -> None:
        """Обработка заработка."""
        # Валидация кошелька
        await self.get_wallet(t.wallet_id, user_id)

    async def _handle_transfer(self, user_id: int, t: Transaction) -> None:
        """Обработка перевода между портфелями."""
        await asyncio.gather(
            # Валидация исходного кошелька
            await self.get_wallet(t.wallet_id, user_id),
            # Валидация целевого кошелька
            await self.get_wallet(t.wallet2_id, user_id),
        )

    async def _handle_input_output(self, user_id: int, t: Transaction) -> None:
        """Обработка ввода-вывода."""
        # Валидация кошелька
        await self.get_wallet(t.wallet_id, user_id)

    async def _validate_create_data(self, data: WalletCreateRequest, user_id: int) -> None:
        """Валидация данных для создания кошелька."""
        # Проверка уникальности имени
        if await self.repo.exists_by_name_and_user(data.name, user_id):
            raise ConflictException('Кошелек с таким именем уже существует')

    async def _validate_update_data(
        self,
        data: WalletUpdateRequest,
        user_id: int,
        wallet: Wallet,
    ) -> None:
        """Валидация данных для обновления кошелька."""
        # Проверка уникальности имени (если изменилось)
        if (data.name != wallet.name and
            await self.repo.exists_by_name_and_user(data.name, user_id)):
                raise ConflictException('Кошелек с таким именем уже существует')
