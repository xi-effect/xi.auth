from typing import Any

import pytest
from faker import Faker
from starlette.testclient import TestClient

from app.users.models.users_db import User
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response


@pytest.mark.anyio()
async def test_user_creation(
    mub_client: TestClient,
    active_session: ActiveSession,
    user_data: dict[str, Any],
) -> None:
    user_id: int = assert_response(
        mub_client.post("/mub/users/", json=user_data),
        expected_code=201,
        expected_json={**user_data, "id": int, "password": None},
    ).json()["id"]

    async with active_session():
        user = await User.find_first_by_id(user_id)
        assert user is not None
        await user.delete()


@pytest.mark.anyio()
@pytest.mark.parametrize(
    ("pass_unique_email", "pass_unique_password", "error"),
    [
        pytest.param(True, False, "Username already in use", id="username"),
        pytest.param(False, True, "Email already in use", id="email"),
    ],
)
async def test_user_creation_conflict(
    faker: Faker,
    mub_client: TestClient,
    user_data: dict[str, Any],
    user: User,
    pass_unique_email: bool,
    pass_unique_password: bool,
    error: str,
) -> None:
    data_modification: dict[str, Any] = {}
    if pass_unique_email:
        data_modification["email"] = faker.email()
    if pass_unique_password:
        data_modification["password"] = faker.password()

    assert_response(
        mub_client.post("/mub/users/", json={**user_data, **data_modification}),
        expected_code=409,
        expected_json={"detail": error},
    )


@pytest.mark.anyio()
async def test_user_getting(
    mub_client: TestClient, user: User, user_data: dict[str, Any]
) -> None:
    assert_response(
        mub_client.get(f"/mub/users/{user.id}/"),
        expected_json={**user_data, "id": user.id, "password": None},
    )


@pytest.mark.anyio()
@pytest.mark.parametrize("pass_email", [False, True], ids=["no_email", "with_email"])
@pytest.mark.parametrize(
    "pass_password", [False, True], ids=["no_password", "with_password"]
)
@pytest.mark.parametrize(
    "pass_profile_data", [False, True], ids=["no_profile_data", "with_profile_data"]
)
async def test_user_updating(
    faker: Faker,
    mub_client: TestClient,
    user_data: dict[str, Any],
    user: User,
    pass_email: bool,
    pass_password: bool,
    pass_profile_data: bool,
) -> None:
    new_user_data: dict[str, Any] = {}
    if pass_email:
        new_user_data["email"] = faker.email()
    if pass_password:
        new_user_data["password"] = faker.password()
    if pass_profile_data:
        new_user_data.update(
            username=faker.username(),
            display_name=faker.name(),
            theme="new_theme",
        )

    assert_response(
        mub_client.patch(f"/mub/users/{user.id}/", json=new_user_data),
        expected_json={**user_data, **new_user_data, "id": user.id, "password": None},
    )


@pytest.mark.anyio()
async def test_user_updating_same_data(
    mub_client: TestClient,
    user_data: dict[str, Any],
    user: User,
) -> None:
    assert_response(
        mub_client.patch(
            f"/mub/users/{user.id}/",
            json=user_data,
        ),
        expected_json={**user_data, "id": user.id, "password": None},
    )


@pytest.mark.anyio()
@pytest.mark.parametrize(
    ("pass_used_email", "pass_used_username", "error"),
    [
        pytest.param(False, True, "Username already in use", id="username"),
        pytest.param(True, False, "Email already in use", id="email"),
    ],
)
async def test_user_updating_conflict(
    faker: Faker,
    mub_client: TestClient,
    other_user: User,
    user: User,
    pass_used_email: bool,
    pass_used_username: bool,
    error: str,
) -> None:
    data_modification: dict[str, Any] = {}
    if pass_used_email:
        data_modification["email"] = other_user.email
    if pass_used_username:
        data_modification["username"] = other_user.username

    assert_response(
        mub_client.patch(f"/mub/users/{user.id}/", json=data_modification),
        expected_code=409,
        expected_json={"detail": error},
    )


@pytest.mark.anyio()
async def test_user_deleting(mub_client: TestClient, user: User) -> None:
    assert_nodata_response(mub_client.delete(f"/mub/users/{user.id}/"))


@pytest.mark.anyio()
@pytest.mark.parametrize("method", ["GET", "PATCH", "DELETE"])
async def test_user_not_found(
    mub_client: TestClient, deleted_user: User, method: str
) -> None:
    assert_response(
        mub_client.request(
            method,
            f"/mub/users/{deleted_user.id}/",
            json={} if method == "PATCH" else None,
        ),
        expected_code=404,
        expected_json={"detail": "User not found"},
    )


@pytest.mark.anyio()
async def test_user_updating_username_in_use(
    mub_client: TestClient,
    user: User,
    other_user: User,
) -> None:
    assert_response(
        mub_client.patch(
            f"/mub/users/{user.id}/", json={"username": other_user.username}
        ),
        expected_code=409,
        expected_json={"detail": "Username already in use"},
    )


@pytest.mark.anyio()
async def test_user_creation_invalid_mub_key(
    client: TestClient,
    user_data: dict[str, Any],
    invalid_mub_key_headers: dict[str, Any] | None,
) -> None:
    assert_response(
        client.post(
            "/mub/users/",
            json=user_data,
            headers=invalid_mub_key_headers,
        ),
        expected_json={"detail": "Invalid key"},
        expected_code=401,
    )


@pytest.mark.parametrize("method", ["GET", "PATCH", "DELETE"])
@pytest.mark.anyio()
async def test_user_operations_invalid_mub_key(
    client: TestClient,
    user: User,
    invalid_mub_key_headers: dict[str, Any] | None,
    method: str,
) -> None:
    assert_response(
        client.request(
            method,
            f"/mub/users/{user.id}/",
            json={},
            headers=invalid_mub_key_headers,
        ),
        expected_json={"detail": "Invalid key"},
        expected_code=401,
    )
