# ruff: noqa: A002
# pyright: reportAttributeAccessIssue=false

# TODO: Логирование

from collections.abc import Sequence
from typing import TYPE_CHECKING, TypeVar

from pydantic import BaseModel
from sqlalchemy import delete, exists, select, update
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import expression, func

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


Id = TypeVar('Id', int, str)


class BaseRepository[Model, CreateSchema: BaseModel, UpdateSchema: BaseModel]:
    """Базовый асинхронный CRUD репозиторий для SQLAlchemy.

    Примечание:
        - Требуется commit для сохранения изменений
        - Возвращает None если объект не найден
    """

    def __init__(self, model: type[Model], session: 'AsyncSession') -> None:
        self.model = model
        self.session = session

    async def get(self, id: Id, relations: tuple[str, ...] = ()) -> Model | None:
        """Получить объект по ID."""
        stmt = select(self.model).where(self.model.id == id)

        for relation in relations:
            stmt = stmt.options(selectinload(getattr(self.model, relation)))

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by(
        self,
        *where: expression.ColumnElement[bool],
        order_by: Sequence[expression.ColumnElement] | None = None,
        relations: tuple[str, ...] = (),
    ) -> Model | None:
        """Получить объект по условию."""
        stmt = select(self.model)

        if where:
            stmt = stmt.where(*where)

        if order_by:
            stmt = stmt.order_by(*order_by)

        for relation in relations:
            stmt = stmt.options(selectinload(getattr(self.model, relation)))

        stmt = stmt.limit(1)
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def get_many(
        self,
        ids: Sequence[Id],
        relations: tuple[str, ...] = (),
    ) -> list[Model]:
        """Получить список объектов по списку ID."""
        if not ids:
            return []

        stmt = select(self.model).where(self.model.id.in_(ids))

        for relation in relations:
            stmt = stmt.options(selectinload(getattr(self.model, relation)))

        result = await self.session.execute(stmt)
        return result.unique().scalars().all()

    async def get_many_by(
        self,
        *where: expression.ColumnElement[bool],
        order_by: Sequence[expression.ColumnElement] | None = None,
        skip: int = 0,
        limit: int | None = None,
        relations: tuple[str, ...] = (),
    ) -> list[Model]:
        """Получить список объектов по условию."""
        stmt = select(self.model)

        if where:
            stmt = stmt.where(*where)

        if order_by:
            stmt = stmt.order_by(*order_by)

        for relation in relations:
            stmt = stmt.options(selectinload(getattr(self.model, relation)))

        stmt = stmt.offset(skip)
        if limit:
            stmt = stmt.limit(limit)

        result = await self.session.execute(stmt)
        return result.unique().scalars().all()

    async def create(self, data: CreateSchema) -> Model:
        """Создать объект."""
        obj = self.model(**data.model_dump())
        self.session.add(obj)
        return obj

    async def create_many(self, objects: list[CreateSchema]) -> list[Model]:
        """Создать несколько объектов."""
        objs = [self.model(**obj.model_dump()) for obj in objects]
        self.session.add_all(objs)
        return objs

    async def update(
        self,
        id: Id,
        data: UpdateSchema,
        *,
        exclude_unset: bool = True,
    ) -> Model | None:
        """Обновить объект."""
        update_data = data.model_dump(exclude_unset=exclude_unset)

        stmt = (
            update(self.model)
            .where(self.model.id == id)
            .values(**update_data)
            .returning(self.model)
        )

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_many(
        self,
        ids: list[Id],
        data: UpdateSchema,
        *,
        exclude_unset: bool = True,
    ) -> list[Model]:
        """Обновить несколько объектов."""
        if not ids:
            return []

        update_data = data.model_dump(exclude_unset=exclude_unset)

        stmt = (
            update(self.model)
            .where(self.model.id.in_(ids))
            .values(**update_data)
            .returning(self.model)
        )

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def delete(self, id: Id) -> bool:
        """Удалить объект по ID."""
        stmt = delete(self.model).where(self.model.id == id).returning(self.model.id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def delete_by(
        self,
        *where: expression.ColumnElement[bool],
        order_by: Sequence[expression.ColumnElement] | None = None,
    ) -> bool:
        """Удалить объект по условию."""
        stmt = delete(self.model)

        if where:
            stmt = stmt.where(*where)

        if order_by:
            stmt = stmt.order_by(*order_by)

        stmt = stmt.limit(1).returning(self.model.id)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def delete_many(self, ids: Sequence[Id]) -> list[Id]:
        """Удалить несколько объектов по списку ID, вернуть список ID удалённых."""
        if not ids:
            return []

        stmt = delete(self.model).where(self.model.id.in_(ids)).returning(self.model.id)
        result = await self.session.execute(stmt)
        return [row[0] for row in result.all()]

    async def delete_many_by(
        self,
        *where: expression.ColumnElement[bool],
        order_by: Sequence[expression.ColumnElement] | None = None,
    ) -> list[Id]:
        """Удалить объекты по условию, вернуть список ID удалённых."""
        stmt = delete(self.model)

        if where:
            stmt = stmt.where(*where)

        if order_by:
            stmt = stmt.order_by(*order_by)

        stmt = stmt.returning(self.model.id)

        result = await self.session.execute(stmt)
        return [row[0] for row in result.all()]

    async def count(
        self,
        *where: expression.ColumnElement[bool],
    ) -> int:
        """Подсчитать количество объектов."""
        stmt = select(func.count()).select_from(self.model)

        if where:
            stmt = stmt.where(*where)

        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def paginate(
        self,
        *where: expression.ColumnElement[bool],
        page: int = 1,
        page_size: int = 20,
        order_by: Sequence[expression.ColumnElement] | None = None,
        relations: tuple[str, ...] = (),
    ) -> tuple[list[Model], int]:
        """Пагинация с подсчетом общего количества."""
        # Подсчет общего количества
        total = await self.count(*where)

        # Получение данных
        skip = (page - 1) * page_size
        items = await self.get_many_by(
            *where,
            order_by=order_by,
            relations=relations,
            skip=skip,
            limit=page_size,
        )

        return items, total

    async def get_or_create(
        self,
        defaults: CreateSchema | None = None,
        **kwargs: object,
    ) -> Model:
        """Получить объект или создать новый."""
        # Строим условия поиска из kwargs
        conditions = []
        for key, value in kwargs.items():
            if hasattr(self.model, key):
                conditions.append(getattr(self.model, key) == value)

        # Пытаемся найти существующий объект
        obj = await self.get_by(*conditions)
        if obj:
            return obj

        # Создаем новый объект
        create_data = defaults.model_dump() if defaults else {}

        # Добавляем kwargs в create_data
        for key, value in kwargs.items():
            if key not in create_data and hasattr(self.model, key):
                create_data[key] = value

        obj = self.model(**create_data)
        self.session.add(obj)
        return obj

    async def exists(self, id: Id) -> bool:
        """Проверить существование объекта по ID."""
        stmt = select(exists().where(self.model.id == id))
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def exists_by(self, *where: expression.ColumnElement[bool]) -> bool:
        """Проверить существование объекта по условию."""
        stmt = select(exists().where(*where))
        result = await self.session.execute(stmt)
        return result.scalar_one()
