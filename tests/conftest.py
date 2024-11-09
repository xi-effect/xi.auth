from collections.abc import AsyncIterator, Iterator

import pytest
from sqlalchemy import delete
from starlette.testclient import TestClient

from app.common.config import COOKIE_DOMAIN, MUB_KEY
from app.main import app
from app.users.models.users_db import User
from tests.common.active_session import ActiveSession

pytest_plugins = (
    "anyio",
    "tests.common.active_session",
    "tests.common.faker_ext",
    "tests.common.mock_stack",
)


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(autouse=True)
async def _reset_database(active_session: ActiveSession) -> AsyncIterator[None]:
    async with active_session() as session:
        yield
        await session.execute(delete(User))


@pytest.fixture(scope="session", autouse=True)
def client() -> Iterator[TestClient]:
    with TestClient(app, base_url=f"http://{COOKIE_DOMAIN}") as client:
        yield client


@pytest.fixture(scope="session")
def mub_client(client: TestClient) -> TestClient:
    return TestClient(
        client.app,
        base_url=f"http://{COOKIE_DOMAIN}",
        headers={"X-MUB-Secret": MUB_KEY},
    )
