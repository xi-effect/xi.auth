from __future__ import annotations

from collections.abc import Sequence
from contextvars import ContextVar, Token
from types import TracebackType
from typing import Any, Self, TypeVar

from sqlalchemy import Row, Select, select
from sqlalchemy.orm import Session, sessionmaker as Sessionmaker
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

session: ContextVar[Session | None] = ContextVar("session", default=None)


class DBSessionMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, sessionmaker: Sessionmaker[Session]) -> None:
        super().__init__(app)
        self.sessionmaker: Sessionmaker[Session] = sessionmaker
        self.token: Token[Session | None] | None = None

    def __enter__(self) -> Self:
        self.token = session.set(self.sessionmaker())
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,  # noqa: U100
        exc_tb: TracebackType | None,  # noqa: U100
    ) -> None:
        current_session = session.get()
        if current_session is None:
            raise RuntimeError("Session is None before closing")

        if exc_type is not None:
            current_session.rollback()
        else:
            current_session.commit()

        current_session.close()
        # might need a `session.reset(self.token)`

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        with self:
            response = await call_next(request)
        return response


t = TypeVar("t", bound=Any)


class DBController:
    @property
    def session(self) -> Session:
        """Return an instance of Session local to the current context"""
        result = session.get()
        if result is None:
            raise ValueError("Session not initialized")
        return result

    def get_first(self, stmt: Select[tuple[t]]) -> t | None:
        return self.session.scalars(stmt).first()

    def get_first_row(self, stmt: Select[Any]) -> Row[Any] | None:
        return self.session.execute(stmt).first()

    def get_all(self, stmt: Select[tuple[t]]) -> list[t]:
        return self.session.scalars(stmt).all()  # type: ignore[return-value]

    def get_all_rows(self, stmt: Select[Any]) -> Sequence[Row[Any]]:
        return self.session.execute(stmt).all()

    def get_paginated(self, stmt: Select[tuple[t]], offset: int, limit: int) -> list[t]:
        return self.get_all(stmt.offset(offset).limit(limit))

    def get_paginated_rows(
        self,
        stmt: Select[Any],
        offset: int,
        limit: int,
    ) -> Sequence[Row[Any]]:
        return self.get_all_rows(stmt.offset(offset).limit(limit))


db: DBController = DBController()


class MappingBase:
    @classmethod
    def create(cls, **kwargs: Any) -> Self:
        entry = cls(**kwargs)  # noqa
        db.session.add(entry)
        db.session.flush()
        return entry

    @classmethod
    def select_by_kwargs(cls, *order_by: Any, **kwargs: Any) -> Select[tuple[Self]]:
        if len(order_by) == 0:
            return select(cls).filter_by(**kwargs)
        return select(cls).filter_by(**kwargs).order_by(*order_by)

    @classmethod
    def find_first_by_kwargs(cls, *order_by: Any, **kwargs: Any) -> Self | None:
        return db.get_first(cls.select_by_kwargs(*order_by, **kwargs))

    @classmethod
    def find_all_by_kwargs(cls, *order_by: Any, **kwargs: Any) -> list[Self]:
        return db.get_all(cls.select_by_kwargs(*order_by, **kwargs))

    @classmethod
    def find_paginated_by_kwargs(
        cls,
        offset: int,
        limit: int,
        *order_by: Any,
        **kwargs: Any,
    ) -> list[Self]:
        return db.get_paginated(
            cls.select_by_kwargs(*order_by, **kwargs),
            offset=offset,
            limit=limit,
        )

    def update(self, **kwargs: Any) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)

    def delete(self) -> None:
        db.session.delete(self)
        db.session.flush()
