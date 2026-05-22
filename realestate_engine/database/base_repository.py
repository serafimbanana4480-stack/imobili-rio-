"""Generic base repository with common CRUD operations - DRY refactor for repository.py."""

from typing import Optional, List, Dict, Any, Type, TypeVar, Generic
from sqlalchemy import select, update, delete
from sqlalchemy.orm import DeclarativeBase, Session
from loguru import logger

from realestate_engine.database.repository import transaction_scope

ModelType = TypeVar("ModelType", bound=DeclarativeBase)


class BaseRepository(Generic[ModelType]):
    """Generic repository with common CRUD operations.

    Replaces 20+ repetitive query patterns in DatabaseRepository.
    Specific repositories inherit and add domain-specific methods.
    """

    def __init__(self, model: Type[ModelType], session_factory):
        self.model = model
        self.session_factory = session_factory

    def get_all(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 1000,
        offset: int = 0,
        order_by: Optional[str] = None,
        order_desc: bool = False,
    ) -> List[ModelType]:
        with self.session_factory() as session:
            query = select(self.model)
            if filters:
                for key, value in filters.items():
                    if hasattr(self.model, key) and value is not None:
                        query = query.where(getattr(self.model, key) == value)
            if order_by and hasattr(self.model, order_by):
                column = getattr(self.model, order_by)
                query = query.order_by(column.desc() if order_desc else column.asc())
            query = query.offset(offset).limit(limit)
            return list(session.execute(query).scalars().all())

    def get_by_id(self, id: Any) -> Optional[ModelType]:
        with self.session_factory() as session:
            return session.execute(
                select(self.model).where(self.model.id == id)
            ).scalar_one_or_none()

    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        from sqlalchemy import func
        with self.session_factory() as session:
            query = select(func.count()).select_from(self.model)
            if filters:
                for key, value in filters.items():
                    if hasattr(self.model, key) and value is not None:
                        query = query.where(getattr(self.model, key) == value)
            return session.execute(query).scalar() or 0

    def create(self, obj: ModelType) -> ModelType:
        with transaction_scope(self.session_factory()) as session:
            session.add(obj)
            return obj

    def create_batch(self, objs: List[ModelType]) -> List[ModelType]:
        with transaction_scope(self.session_factory()) as session:
            session.add_all(objs)
            return objs

    def update(self, id: Any, updates: Dict[str, Any]) -> bool:
        with transaction_scope(self.session_factory()) as session:
            valid_keys = {c.name for c in self.model.__table__.columns}
            filtered = {k: v for k, v in updates.items() if k in valid_keys}
            if not filtered:
                return False
            result = session.execute(
                update(self.model).where(self.model.id == id).values(**filtered)
            )
            return result.rowcount > 0

    def delete(self, id: Any) -> bool:
        with transaction_scope(self.session_factory()) as session:
            result = session.execute(
                delete(self.model).where(self.model.id == id)
            )
            return result.rowcount > 0

    def exists(self, filters: Dict[str, Any]) -> bool:
        return self.count(filters) > 0
