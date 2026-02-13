import asyncio
from pathlib import Path
import sys

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


from app.core.config import settings
from app.models import Base

config = context.config
target_metadata = Base.metadata


async def run_migrations() -> None:
    """Запуск миграций."""
    engine = create_async_engine(
        settings.db_url,
        pool_pre_ping=True,
        echo=False,
    )
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)


def do_run_migrations(connection) -> None:
    """Выполнение миграций через синхронное соединение."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    raise RuntimeError('Offline mode не настроен')

asyncio.run(run_migrations())
