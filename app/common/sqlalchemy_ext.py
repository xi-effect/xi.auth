from __future__ import annotations

from collections.abc import Sequence
from contextvars import ContextVar
from typing import Any, Self, TypeVar

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

session_context: ContextVar[AsyncSession | None] = ContextVar("session", default=None)

t = TypeVar("t", bound=Any)


class DBController:
    @property
    def session(self) -> AsyncSession:
        """Return an instance of Session local to the current context"""
        session = session_context.get()
        if session is None:
            raise ValueError("Session not initialized")
        return session

    async def get_first(self, stmt: Select[Any]) -> Any | None:
        return (await self.session.execute(stmt)).scalars().first()

    async def get_all(self, stmt: Select[Any]) -> Sequence[Any]:
        return (await self.session.execute(stmt)).scalars().all()

    async def get_paginated(
        self, stmt: Select[Any], offset: int, limit: int
    ) -> Sequence[Any]:
        return await self.get_all(stmt.offset(offset).limit(limit))


db: DBController = DBController()


class MappingBase:
    @classmethod
    async def create(cls, **kwargs: Any) -> Self:
        entry = cls(**kwargs)  # noqa
        db.session.add(entry)
        await db.session.flush()
        return entry

    @classmethod
    def select_by_kwargs(cls, *order_by: Any, **kwargs: Any) -> Select[tuple[Self]]:
        if len(order_by) == 0:
            return select(cls).filter_by(**kwargs)
        return select(cls).filter_by(**kwargs).order_by(*order_by)

    @classmethod
    async def find_first_by_id(cls, *keys: Any) -> Self | None:
        return await db.session.get(cls, *keys)

    @classmethod
    async def find_first_by_kwargs(cls, *order_by: Any, **kwargs: Any) -> Self | None:
        return await db.get_first(cls.select_by_kwargs(*order_by, **kwargs))

    @classmethod
    async def find_all_by_kwargs(cls, *order_by: Any, **kwargs: Any) -> Sequence[Self]:
        return await db.get_all(cls.select_by_kwargs(*order_by, **kwargs))

    @classmethod
    async def find_paginated_by_kwargs(
        cls,
        offset: int,
        limit: int,
        *order_by: Any,
        **kwargs: Any,
    ) -> Sequence[Self]:
        return await db.get_paginated(
            cls.select_by_kwargs(*order_by, **kwargs),
            offset=offset,
            limit=limit,
        )

    def update(self, **kwargs: Any) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)

    async def delete(self) -> None:
        await db.session.delete(self)
        await db.session.flush()
