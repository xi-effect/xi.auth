from collections.abc import AsyncIterator, Iterator
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from typing import Protocol

import pytest
from faker import Faker
from faker.providers import internet
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.testclient import TestClient

from app.common.config import sessionmaker
from app.common.sqla import session_context
from app.main import app

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
