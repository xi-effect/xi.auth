import pytest
from starlette.testclient import TestClient

from app.models.users_db import User
from tests.conftest import ActiveSession
from tests.utils import assert_response


@pytest.mark.anyio()
async def test_getting_profile_by_id(
    authorized_client: TestClient,
    other_user: User,
) -> None:
    assert_response(
        authorized_client.get(f"/api/users/by_id/{other_user.id}/profile/"),
        expected_json={
            "id": other_user.id,
            "username": other_user.username,
            "display_name": other_user.display_name,
        },
    )


@pytest.mark.anyio()
async def test_getting_profile_by_id_not_found(
    authorized_client: TestClient,
    other_user: User,
    active_session: ActiveSession,
) -> None:
    async with active_session():
        await other_user.delete()
    assert_response(
        authorized_client.get(f"/api/users/by_id/{other_user.id}/profile/"),
        expected_json={"detail": "User not found"},
        expected_code=404,
    )


@pytest.mark.anyio()
async def test_getting_profile_by_id_unauthorized(
    client: TestClient,
    other_user: User,
) -> None:
    assert_response(
        client.get(f"/api/users/by_id/{other_user.id}/profile/"),
        expected_json={"detail": "Authorization is missing"},
        expected_code=401,
    )


@pytest.mark.anyio()
async def test_getting_profile_by_username(
    authorized_client: TestClient,
    other_user: User,
) -> None:
    assert_response(
        authorized_client.get(f"/api/users/by_username/{other_user.username}/profile/"),
        expected_json={
            "id": other_user.id,
            "username": other_user.username,
            "display_name": other_user.display_name,
        },
    )


@pytest.mark.anyio()
async def test_getting_profile_by_username_not_found(
    authorized_client: TestClient,
    other_user: User,
    active_session: ActiveSession,
) -> None:
    async with active_session():
        await other_user.delete()
    assert_response(
        authorized_client.get(f"/api/users/by_username/{other_user.username}/profile/"),
        expected_json={"detail": "User not found"},
        expected_code=404,
    )


@pytest.mark.anyio()
async def test_getting_profile_by_username_unauthorized(
    client: TestClient,
    other_user: User,
) -> None:
    assert_response(
        client.get(f"/api/users/by_username/{other_user.username}/profile/"),
        expected_json={"detail": "Authorization is missing"},
        expected_code=401,
    )
