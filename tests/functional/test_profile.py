from typing import Any

import pytest
from faker import Faker
from starlette.testclient import TestClient

from app.models.users_db import User
from tests.utils import assert_response

BASE_LINK: str = "/api/users/current"


@pytest.mark.anyio()
@pytest.mark.parametrize(
    "test_username", [False, True], ids=["no_username", "with_username"]
)
@pytest.mark.parametrize(
    "test_display_name", [False, True], ids=["no_display_name", "with_display_name"]
)
async def test_profile_updating(
    faker: Faker,
    authorized_client: TestClient,
    user_data: dict[str, Any],
    user: User,
    test_username: bool,
    test_display_name: bool,
) -> None:
    update_data = {}
    if test_username:
        update_data["username"] = faker.profile(fields=["username"])["username"]
    if test_display_name:
        update_data["display_name"] = faker.name()

    assert_response(
        authorized_client.patch(f"{BASE_LINK}/profile/", json=update_data),
        expected_json={**user_data, **update_data, "id": user.id, "password": None},
    )


@pytest.mark.anyio()
async def test_updating_conflict(
    authorized_client: TestClient,
    user: User,
    other_user: User,
) -> None:
    assert_response(
        authorized_client.patch(
            f"{BASE_LINK}/profile/", json={"username": other_user.username}
        ),
        expected_code=409,
        expected_json={"detail": "Username already in use"},
    )


@pytest.mark.anyio()
@pytest.mark.parametrize("theme", [None, "dark"], ids=["default_theme", "dark_theme"])
async def test_theme_changing(
    authorized_client: TestClient,
    user: User,
    theme: str | None,
) -> None:
    assert_response(
        authorized_client.patch(
            f"{BASE_LINK}/customization/", json={"theme": theme} if theme else {}
        ),
        expected_json={"theme": theme or user.theme, "id": user.id},
    )
