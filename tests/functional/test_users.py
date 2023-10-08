from typing import Any

import pytest
from faker import Faker
from starlette.testclient import TestClient

from app.models.users_db import User
from tests.conftest import ActiveSession
from tests.utils import assert_response


@pytest.mark.anyio()
async def test_creation(
    client: TestClient,
    active_session: ActiveSession,
    user_data: dict[str, Any],
) -> None:
    user_id: int = assert_response(
        client.post("/mub/users", json=user_data),
        expected_json={**user_data, "id": int, "password": None},
    ).json()["id"]

    async with active_session():
        user = await User.find_first_by_id(user_id)
        assert user is not None
        await user.delete()


def test_getting(client: TestClient, user: User, user_data: dict[str, Any]) -> None:
    assert_response(
        client.get(f"/mub/users/{user.id}"),
        expected_json={**user_data, "id": user.id, "password": None},
    )


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

    assert_response(
        client.put(f"/mub/users/{user.id}", json=new_user_data),
        expected_json={**user_data, **new_user_data, "id": user.id, "password": None},
    )
