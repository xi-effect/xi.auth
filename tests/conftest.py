from collections.abc import AsyncIterator, Iterator
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from typing import Any, Protocol, TypeVar

import pytest
from faker import Faker
from faker.providers import internet
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.testclient import TestClient

from app.common.config import sessionmaker
from app.common.sqla import session_context
from app.main import app
from app.models.sessions_db import Session
from app.models.users_db import User
from app.utils.authorization import AUTH_HEADER

pytest_plugins = ("anyio",)


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(autouse=True)
def _setup_faker(faker: Faker) -> None:
    faker.add_provider(internet)


class ActiveSession(Protocol):
    def __call__(self) -> AbstractAsyncContextManager[AsyncSession]:
        pass


@pytest.fixture(scope="session")
def active_session() -> ActiveSession:
    @asynccontextmanager
    async def active_session_inner() -> AsyncIterator[AsyncSession]:
        async with sessionmaker.begin() as session:
            session_context.set(session)
            yield session

    return active_session_inner


@pytest.fixture()
def client() -> Iterator[TestClient]:
    with TestClient(app) as client:
        yield client


@pytest.fixture()
async def user_data(faker: Faker) -> dict[str, Any]:
    return {"email": faker.email(), "password": faker.password()}


@pytest.fixture()
async def user(
    active_session: ActiveSession,
    user_data: dict[str, Any],
) -> User:
    user_data = {**user_data, "password": User.generate_hash(user_data["password"])}
    async with active_session():
        return await User.create(**user_data)


@pytest.fixture()
async def other_user(
    faker: Faker,
    active_session: ActiveSession,
) -> User:
    async with active_session():
        return await User.create(
            email=faker.email(),
            password=User.generate_hash(faker.password()),
        )


T = TypeVar("T", covariant=True)


class Factory(Protocol[T]):
    async def __call__(self, **kwargs: Any) -> T:  # noqa: U100  # bug
        pass


@pytest.fixture()
async def session_factory(
    active_session: ActiveSession, user: User
) -> Factory[Session]:
    async def session_factory_inner(**kwargs: Any) -> Session:
        async with active_session():
            return await Session.create(user_id=user.id, **kwargs)

    return session_factory_inner


@pytest.fixture()
async def session(session_factory: Factory[Session]) -> Session:
    return await session_factory()


@pytest.fixture()
def session_token(session: Session) -> str:
    return session.token


@pytest.fixture()
def authorized_client(session_token: str) -> Iterator[TestClient]:
    with TestClient(app, headers={AUTH_HEADER: session_token}) as client:
        yield client


@pytest.fixture()
async def other_session(active_session: ActiveSession, other_user: User) -> Session:
    async with active_session():
        return await Session.create(user_id=other_user.id)


@pytest.fixture()
def other_session_token(other_session: Session) -> str:
    return other_session.token


@pytest.fixture()
def other_client(other_session_token: str) -> Iterator[TestClient]:
    with TestClient(app, headers={AUTH_HEADER: other_session_token}) as client:
        yield client


@pytest.fixture()
async def invalid_session(session_factory: Factory[Session]) -> Session:
    return await session_factory(disabled=True)


@pytest.fixture()
def invalid_token(invalid_session: Session) -> str:
    return invalid_session.token


@pytest.fixture(autouse=True)
async def _reset_database(active_session: ActiveSession) -> None:
    async with active_session() as session:
        await session.execute(delete(User))
