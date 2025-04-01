from collections.abc import Iterator
from typing import Any

import pytest
from faker import Faker
from fastapi.testclient import TestClient

from app.common.config import settings
from app.users.models.sessions_db import Session
from app.users.models.users_db import User
from app.users.utils.authorization import AUTH_COOKIE_NAME, AUTH_HEADER_NAME
from tests.common.active_session import ActiveSession
from tests.common.types import Factory, PytestRequest


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


@pytest.fixture()
async def session_factory(
    active_session: ActiveSession, user: User
) -> Factory[Session]:  # TODO used in unit tests for users
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
def authorized_client_base(client: TestClient) -> TestClient:
    return TestClient(client.app, base_url=f"http://{settings.cookie_domain}")


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
def other_client_base(client: TestClient) -> TestClient:
    return TestClient(client.app, base_url=f"http://{settings.cookie_domain}")


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
