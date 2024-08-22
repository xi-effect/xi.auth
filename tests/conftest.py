from collections.abc import AsyncIterator, Iterator
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from typing import Any, Protocol, TypeVar

import pytest
import rstr
from faker import Faker
from faker.providers import BaseProvider, internet
from faker_file.providers import webp_file  # type: ignore[import-untyped]
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.testclient import TestClient

from app.common.config import COOKIE_DOMAIN, sessionmaker
from app.common.sqlalchemy_ext import session_context
from app.main import app
from app.users.models.users_db import User
from tests.mock_stack import MockStack

pytest_plugins = ("anyio",)


@pytest.fixture()
def mock_stack() -> Iterator[MockStack]:
    with MockStack() as stack:
        yield stack


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


class RegexGeneratorProvider(BaseProvider):
    def generate_regex(self, pattern: str) -> str:
        return rstr.xeger(pattern)

    def username(self) -> str:
        return self.generate_regex("^[a-z0-9_.]{4,30}$")


@pytest.fixture(scope="session", autouse=True)
def _setup_faker(faker: Faker) -> None:
    faker.add_provider(internet)
    faker.add_provider(webp_file.GraphicWebpFileProvider)
    faker.add_provider(RegexGeneratorProvider)


@pytest.fixture(scope="session")
def faker(_session_faker: Faker) -> Faker:
    return _session_faker


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


@pytest.fixture(autouse=True)
async def _reset_database(active_session: ActiveSession) -> AsyncIterator[None]:
    async with active_session() as session:
        yield
        await session.execute(delete(User))


@pytest.fixture(scope="session")
def client() -> Iterator[TestClient]:
    with TestClient(app, base_url=f"http://{COOKIE_DOMAIN}") as client:
        yield client


T = TypeVar("T", covariant=True)


class Factory(Protocol[T]):
    async def __call__(self, **kwargs: Any) -> T:  # noqa: U100  # bug
        pass
