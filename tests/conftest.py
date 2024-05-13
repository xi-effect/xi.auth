from collections.abc import AsyncIterator, Iterator
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from typing import Any, Protocol, TypeVar

import pytest
import rstr
from faker import Faker
from faker.providers import BaseProvider, internet
from faker_file.providers import webp_file  # type: ignore[import-untyped]
from fastapi.testclient import TestClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.config import COOKIE_DOMAIN, MUB_KEY, sessionmaker
from app.common.sqla import session_context
from app.main import app
from app.models.sessions_db import Session
from app.models.users_db import User
from app.utils.authorization import AUTH_COOKIE_NAME, AUTH_HEADER_NAME
from tests.mock_stack import MockStack
from tests.utils import PytestRequest

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


@pytest.fixture(scope="session")
def mub_client() -> Iterator[TestClient]:
    with TestClient(
        app, base_url=f"http://{COOKIE_DOMAIN}", headers={"X-MUB-Secret": MUB_KEY}
    ) as client:
        yield client


@pytest.fixture()
async def user_data(faker: Faker) -> dict[str, Any]:
    return {
        "username": faker.username(),
        "email": faker.email(),
        "password": faker.password(),
    }


@pytest.fixture()
async def user(
    active_session: ActiveSession,
    user_data: dict[str, Any],
) -> User:
    async with active_session():
        return await User.create(
            **{**user_data, "password": User.generate_hash(user_data["password"])},
        )


@pytest.fixture()
async def other_user_data(faker: Faker) -> dict[str, Any]:
    return {
        "username": faker.username(),
        "email": faker.email(),
        "password": faker.password(),
    }


@pytest.fixture()
async def other_user(
    faker: Faker,
    active_session: ActiveSession,
    other_user_data: dict[str, Any],
) -> User:
    async with active_session():
        return await User.create(
            **{
                **other_user_data,
                "password": User.generate_hash(other_user_data["password"]),
            },
        )


@pytest.fixture(scope="session")
async def deleted_user(
    faker: Faker,
    active_session: ActiveSession,
) -> User:
    async with active_session():
        user = await User.create(
            username=faker.username(),
            email=faker.email(),
            password=User.generate_hash(faker.password()),
        )
        await user.delete()
    return user


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


@pytest.fixture(params=[False, True], ids=["headers", "cookies"])
def use_cookie_auth(request: PytestRequest[bool]) -> bool:
    return request.param


@pytest.fixture(scope="session")
def authorized_client_base() -> Iterator[TestClient]:
    with TestClient(app, base_url=f"http://{COOKIE_DOMAIN}") as client:
        yield client


@pytest.fixture()
def authorized_client(
    authorized_client_base: TestClient,
    session_token: str,
    use_cookie_auth: bool,
) -> Iterator[TestClient]:
    # property setter allows it, but mypy doesn't get it
    if use_cookie_auth:
        authorized_client_base.cookies = {  # type: ignore[assignment]
            AUTH_COOKIE_NAME: session_token
        }
        yield authorized_client_base
        authorized_client_base.cookies = {}  # type: ignore[assignment]
    else:
        authorized_client_base.headers = {  # type: ignore[assignment]
            AUTH_HEADER_NAME: session_token
        }
        yield authorized_client_base
        authorized_client_base.headers = {}  # type: ignore[assignment]


@pytest.fixture()
async def other_session(active_session: ActiveSession, other_user: User) -> Session:
    async with active_session():
        return await Session.create(user_id=other_user.id)


@pytest.fixture()
def other_session_token(other_session: Session) -> str:
    return other_session.token


@pytest.fixture(scope="session")
def other_client_base() -> Iterator[TestClient]:
    with TestClient(app, base_url=f"http://{COOKIE_DOMAIN}") as client:
        yield client


@pytest.fixture()
def other_client(other_client_base: TestClient, other_session_token: str) -> TestClient:
    # property setter allows it, but mypy doesn't get it
    other_client_base.cookies = {  # type: ignore[assignment]
        AUTH_COOKIE_NAME: other_session_token
    }
    return other_client_base


@pytest.fixture()
async def invalid_session(session_factory: Factory[Session]) -> Session:
    return await session_factory(disabled=True)


@pytest.fixture()
def invalid_token(invalid_session: Session) -> str:
    return invalid_session.token


@pytest.fixture(params=[True, False])
def invalid_mub_key_headers(
    request: PytestRequest[bool], faker: Faker
) -> dict[str, Any] | None:
    if request.param:
        return {"X-MUB-Secret": faker.pystr()}
    return None
