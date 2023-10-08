from typing import Any

import pytest
from pydantic_marshals.contains import assert_contains
from starlette.testclient import TestClient

from app.models.sessions_db import Session
from app.models.users_db import User
from app.utils.authorization import AUTH_HEADER
from tests.conftest import ActiveSession


async def assert_session(xi_id_header: str, invalid: bool = False) -> None:
    session = await Session.find_first_by_kwargs(token=xi_id_header)
    assert session is not None
    assert session.invalid == invalid


@pytest.mark.anyio()
async def test_signup(
    client: TestClient,
    active_session: ActiveSession,
    user_data: dict[str, Any],
) -> None:
    response = client.post("/api/signup", json=user_data)
    assert response.status_code == 200
    assert_contains(response.json(), {**user_data, "id": int, "password": None})
    assert_contains(response.headers, {AUTH_HEADER: str})

    async with active_session():
        await assert_session(response.headers[AUTH_HEADER])

        user = await User.find_first_by_id(response.json()["id"])
        assert user is not None
        await user.delete()


@pytest.mark.anyio()
async def test_signin(
    client: TestClient,
    active_session: ActiveSession,
    user_data: dict[str, Any],
    user: User,
) -> None:
    response = client.post("/api/signin", json=user_data)
    assert response.status_code == 200, (response.json(), user_data)
    assert_contains(response.json(), {**user_data, "id": user.id, "password": None})
    assert_contains(response.headers, {AUTH_HEADER: str})

    async with active_session():
        await assert_session(response.headers[AUTH_HEADER])


@pytest.mark.anyio()
async def test_signout(
    authorized_client: TestClient,
    active_session: ActiveSession,
    session_token: str,
) -> None:
    response = authorized_client.post("/api/signout")
    assert response.status_code == 200
    assert response.json() == {"a": True}

    async with active_session():
        await assert_session(session_token, invalid=True)


def test_no_auth_header(client: TestClient) -> None:
    response = client.post("/api/signout")
    assert response.status_code == 401
    assert_contains(response.json(), {"detail": "X-XI-ID header is missing"})


def test_invalid_session(client: TestClient, invalid_token: str) -> None:
    response = client.post("/api/signout", headers={AUTH_HEADER: invalid_token})
    assert response.status_code == 401
    assert_contains(response.json(), {"detail": "Session is invalid"})
