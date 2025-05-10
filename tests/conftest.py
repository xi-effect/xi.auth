from collections.abc import AsyncIterator, Iterator
from typing import Any, BinaryIO

import pytest
from faker import Faker
from faker_file.providers.pdf_file.generators.pil_generator import (  # type: ignore[import-untyped]
    PilPdfGenerator,
)
from sqlalchemy import delete
from starlette.testclient import TestClient

from app.common.config import settings
from app.main import app
from app.users.models.users_db import User
from tests.common.active_session import ActiveSession

pytest_plugins = (
    "anyio",
    "tests.common.active_session",
    "tests.common.faker_ext",
    "tests.common.mock_stack",
    "tests.common.respx_ext",
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
    with TestClient(app, base_url=f"http://{settings.cookie_domain}") as client:
        yield client


@pytest.fixture(scope="session")
def mub_client(client: TestClient) -> TestClient:
    return TestClient(
        client.app,
        base_url=f"http://{settings.cookie_domain}",
        headers={"X-MUB-Secret": settings.mub_key},
    )


@pytest.fixture()
async def pdf_data(faker: Faker) -> tuple[str, BinaryIO, str]:
    return (
        faker.file_name(extension="pdf"),
        faker.pdf_file(raw=True, pdf_generator_cls=PilPdfGenerator),
        "application/pdf",
    )


@pytest.fixture()
def vacancy_form_data(faker: Faker) -> dict[str, Any]:
    return {
        "position": faker.sentence(nb_words=2),
        "name": faker.name(),
        "telegram": faker.url(),
        "message": faker.sentence(),
    }
