from typing import Any

import pytest
from faker import Faker
from starlette.testclient import TestClient

from app.models.users_db import User
from tests.conftest import ActiveSession
from tests.utils import assert_nodata_response, assert_response


@pytest.mark.anyio()
async def test_user_creation(
    client: TestClient,
    active_session: ActiveSession,
    user_data: dict[str, Any],
) -> None:
    user_id: int = assert_response(
        client.post("/mub/users/", json=user_data),
        expected_json={**user_data, "id": int, "password": None},
    ).json()["id"]

    async with active_session():
        user = await User.find_first_by_id(user_id)
        assert user is not None
        await user.delete()


@pytest.mark.anyio()
@pytest.mark.parametrize(
    ("data_mod", "error"),
    [
        pytest.param({"email": "n@new.new"}, "Username already in use", id="username"),
        pytest.param({"username": "new_one"}, "Email already in use", id="email"),
    ],
)
async def test_user_creation_conflict(
    client: TestClient,
    user_data: dict[str, Any],
    user: User,
    data_mod: dict[str, Any],
    error: str,
) -> None:
    assert_response(
        client.post("/mub/users/", json={**user_data, **data_mod}),
        expected_code=409,
        expected_json={"detail": error},
    )


@pytest.mark.anyio()
async def test_user_getting(
    client: TestClient, user: User, user_data: dict[str, Any]
) -> None:
    assert_response(
        client.get(f"/mub/users/{user.id}/"),
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
    client: TestClient,
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
            username=faker.profile(fields=["username"])["username"],
            display_name=faker.name(),
            theme="new_theme",
        )

    assert_response(
        client.patch(f"/mub/users/{user.id}/", json=new_user_data),
        expected_json={**user_data, **new_user_data, "id": user.id, "password": None},
    )


@pytest.mark.anyio()
async def test_user_deleting(client: TestClient, user: User) -> None:
    assert_nodata_response(client.delete(f"/mub/users/{user.id}/"))


@pytest.mark.anyio()
@pytest.mark.parametrize("method", ["GET", "PATCH", "DELETE"])
async def test_user_not_found(
    client: TestClient, user: User, active_session: ActiveSession, method: str
) -> None:
    async with active_session():
        await user.delete()
    assert_response(
        client.request(
            method, f"/mub/users/{user.id}/", json={} if method == "PATCH" else None
        ),
        expected_code=404,
        expected_json={"detail": "User not found"},
    )


@pytest.mark.anyio()
async def test_username_in_use(
    authorized_client: TestClient,
    user: User,
    other_user: User,
) -> None:
    assert_response(
        authorized_client.patch(
            f"/mub/users/{user.id}/", json={"username": other_user.username}
        ),
        expected_code=409,
        expected_json={"detail": "Username already in use"},
    )
