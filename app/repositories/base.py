from typing import Any, Dict, List, Optional, Type, TypeVar, Generic
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from pydantic import BaseModel


ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    def _apply_relationships(self, query, relationships: Optional[List[str]] = None):
        """Применяет загрузку связей"""
        if relationships:
            for relationship in relationships:
                if hasattr(self.model, relationship):
                    query = query.options(selectinload(getattr(self.model, relationship)))
        return query

    def _apply_filters(self, query, filters: Optional[Dict] = None):
        """Применяет фильтры с поддержкой разных операторов"""
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.where(getattr(self.model, field) == value)
        return query

    async def get_all(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: Optional[int] = None,
        filters: Optional[Dict] = None,
        relationships: Optional[List[str]] = None
    ) -> List[ModelType]:
        """Получить все объекты с пагинацией и фильтрацией"""
        query = select(self.model)
        query = self._apply_filters(query, filters)
        query = self._apply_relationships(query, relationships)

        query = query.offset(skip)
        if limit:
            query = query.limit(limit)

        result = await db.execute(query)
        return result.scalars().all()

    async def get_one(
        self,
        db: AsyncSession,
        filters: Dict[str, Any],
        relationships: Optional[List[str]] = None
    ) -> Optional[ModelType]:
        """Получить один объект по фильтрам"""
        query = select(self.model)
        query = self._apply_filters(query, filters)
        query = self._apply_relationships(query, relationships)

        result = await db.execute(query)
        return result.scalar()

    async def get_by_id(
        self,
        db: AsyncSession,
        id: str | int,
        relationships: Optional[List[str]] = None
    ) -> Optional[ModelType]:
        """Получить объект по ID"""
        return await self.get_one(db, {'id': id}, relationships)

    async def create(self, db: AsyncSession, obj: ModelType) -> ModelType:
        """Создать новый объект"""
        db.add(obj)
        await db.flush()
        await db.refresh(obj)
        return obj

    async def update(
        self,
        db: AsyncSession,
        id: Any,
        update_data: Any
    ) -> Optional[ModelType]:
        """Обновить объект"""
        # Получаем объект
        db_obj = await self.get_by_id(db, id)
        if not db_obj:
            return None

        # Обновляем поля
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(db_obj, field, value)

        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, id: Any) -> bool:
        """Удалить объект"""
        db_obj = await self.get_by_id(db, id)
        if not db_obj:
            return False

        await db.delete(db_obj)
        await db.flush()
        return True

    async def exists(self, db: AsyncSession, filters: Dict[str, Any]) -> bool:
        """Проверить существование объекта по фильтрам"""
        result = await self.get_one(db, filters)
        return result is not None
