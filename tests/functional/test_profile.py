from typing import Any

import pytest
from faker import Faker
from starlette.testclient import TestClient

from app.models.users_db import User
from tests.utils import assert_response


@pytest.mark.anyio()
@pytest.mark.parametrize(
    "pass_username", [False, True], ids=["no_username", "with_username"]
)
@pytest.mark.parametrize(
    "pass_display_name", [False, True], ids=["no_display_name", "with_display_name"]
)
@pytest.mark.parametrize("pass_theme", [False, True], ids=["no_theme", "with_theme"])
async def test_profile_updating(
    faker: Faker,
    authorized_client: TestClient,
    user_data: dict[str, Any],
    user: User,
    pass_username: bool,
    pass_display_name: bool,
    pass_theme: bool,
) -> None:
    update_data: dict[str, Any] = {}
    if pass_username:
        update_data["username"] = faker.profile(fields=["username"])["username"]
    if pass_display_name:
        update_data["display_name"] = faker.name()
    if pass_theme:
        update_data["theme"] = "new_theme"

    assert_response(
        authorized_client.patch("/api/users/current/profile/", json=update_data),
        expected_json={**user_data, **update_data, "id": user.id, "password": None},
    )


@pytest.mark.anyio()
async def test_profile_updating_conflict(
    authorized_client: TestClient,
    user: User,
    other_user: User,
) -> None:
    assert_response(
        authorized_client.patch(
            "/api/users/current/profile/", json={"username": other_user.username}
        ),
        expected_code=409,
        expected_json={"detail": "Username already in use"},
    )
