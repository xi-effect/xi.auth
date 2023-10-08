from typing import Any

import pytest
from starlette.testclient import TestClient

from app.models.sessions_db import Session
from app.models.users_db import User
from app.utils.authorization import AUTH_HEADER
from tests.conftest import ActiveSession
from tests.utils import assert_response


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
    response = assert_response(
        client.post("/api/signup", json=user_data),
        expected_json={**user_data, "id": int, "password": None},
        expected_headers={AUTH_HEADER: str},
    )

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
    response = assert_response(
        client.post("/api/signin", json=user_data),
        expected_json={**user_data, "id": user.id, "password": None},
        expected_headers={AUTH_HEADER: str},
    )

    async with active_session():
        await assert_session(response.headers[AUTH_HEADER])


@pytest.mark.anyio()
async def test_signout(
    authorized_client: TestClient,
    active_session: ActiveSession,
    session_token: str,
) -> None:
    assert_response(
        authorized_client.post("/api/signout"),
        expected_json={"a": True},
    )

    async with active_session():
        await assert_session(session_token, invalid=True)


def test_no_auth_header(client: TestClient) -> None:
    assert_response(
        client.post("/api/signout"),
        expected_code=401,
        expected_json={"detail": "X-XI-ID header is missing"},
    )


def test_invalid_session(client: TestClient, invalid_token: str) -> None:
    assert_response(
        client.post("/api/signout", headers={AUTH_HEADER: invalid_token}),
        expected_code=401,
        expected_json={"detail": "Session is invalid"},
    )
