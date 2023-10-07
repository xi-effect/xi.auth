from collections.abc import AsyncIterator
from typing import Any

import pytest
from faker import Faker
from pydantic_marshals.contains import assert_contains
from starlette.testclient import TestClient

from app.models.users_db import User
from tests.conftest import ActiveSession


@pytest.fixture()
async def user_data(faker: Faker) -> dict[str, Any]:
    return {"email": faker.email(), "password": faker.password()}


@pytest.mark.anyio()
async def test_creation(
    client: TestClient,
    active_session: ActiveSession,
    user_data: dict[str, Any],
) -> None:
    response = client.post("/mub/users", json=user_data)
    assert_contains(response.json(), {**user_data, "id": int, "password": None})

    async with active_session():
        user = await User.find_first_by_id(response.json()["id"])
        assert user is not None
        await user.delete()


@pytest.fixture()
async def user(
    active_session: ActiveSession,
    user_data: dict[str, Any],
) -> AsyncIterator[User]:
    user_data["password"] = User.generate_hash(user_data["password"])
    async with active_session():
        user = await User.create(**user_data)

    yield user

    async with active_session():
        await user.delete()


def test_getting(client: TestClient, user: User, user_data: dict[str, Any]) -> None:
    response = client.get(f"/mub/users/{user.id}")
    assert_contains(response.json(), {**user_data, "id": user.id, "password": None})


@pytest.mark.parametrize("pass_email", [False, True], ids=["no_email", "with_email"])
@pytest.mark.parametrize(
    "pass_password", [False, True], ids=["no_password", "with_password"]
)
def test_updating(
    faker: Faker,
    client: TestClient,
    user_data: dict[str, Any],
    user: User,
    pass_email: bool,
    pass_password: bool,
) -> None:
    new_user_data = {}
    if pass_email:
        new_user_data["email"] = faker.email()
    if pass_password:
        new_user_data["password"] = faker.password()

    response = client.put(f"/mub/users/{user.id}", json=new_user_data)
    assert_contains(
        response.json(), {**user_data, **new_user_data, "id": user.id, "password": None}
    )
