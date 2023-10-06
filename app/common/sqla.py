from __future__ import annotations

from collections.abc import Sequence
from contextvars import ContextVar, Token
from types import TracebackType
from typing import Any, Self, TypeVar

from sqlalchemy import Result, Select, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker as Sessionmaker
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

session: ContextVar[AsyncSession | None] = ContextVar("session", default=None)


class DBSessionMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, sessionmaker: Sessionmaker[AsyncSession]) -> None:
        super().__init__(app)
        self.sessionmaker: Sessionmaker[AsyncSession] = sessionmaker
        self.token: Token[AsyncSession | None] | None = None

    async def __aenter__(self) -> Self:
        self.token = session.set(self.sessionmaker())
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,  # noqa: U100
        exc_tb: TracebackType | None,  # noqa: U100
    ) -> None:
        current_session = session.get()
        if current_session is None:
            raise RuntimeError("Session is None before closing")

        if exc_type is not None:
            await current_session.rollback()
        else:
            await current_session.commit()

        await current_session.close()
        # might need a `session.reset(self.token)`

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        async with self:
            return await call_next(request)


t = TypeVar("t", bound=Any)


class DBController:
    @property
    def session(self) -> AsyncSession:
        """Return an instance of Session local to the current context"""
        result = session.get()
        if result is None:
            raise ValueError("Session not initialized")
        return result

    async def get_first(self, stmt: Select[tuple[t]]) -> t | None:
        result: Result[tuple[t]] = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_all(self, stmt: Select[tuple[t]]) -> Sequence[t]:
        result: Result[tuple[t]] = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_paginated(
        self, stmt: Select[tuple[t]], offset: int, limit: int
    ) -> Sequence[t]:
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
        return await db.get_first(
            cls.select_by_kwargs(*order_by, **kwargs)  # type: ignore[arg-type]  # bug
        )

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
