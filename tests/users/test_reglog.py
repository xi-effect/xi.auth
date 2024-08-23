from typing import Any

import pytest
from starlette.testclient import TestClient

from app.common.config import pochta_producer
from app.users.models.users_db import User
from app.users.utils.authorization import AUTH_COOKIE_NAME, AUTH_HEADER_NAME
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.mock_stack import MockStack
from tests.common.types import PytestRequest
from tests.utils import assert_session, assert_session_from_cookie


@pytest.fixture(params=[False, True], ids=["same_site", "cross_site"])
def is_cross_site(request: PytestRequest[bool]) -> bool:
    return request.param


@pytest.mark.anyio()
async def test_signing_up(
    mock_stack: MockStack,
    client: TestClient,
    active_session: ActiveSession,
    user_data: dict[str, Any],
    is_cross_site: bool,
) -> None:
    pochta_mock = mock_stack.enter_async_mock(pochta_producer, "send_message")

    response = assert_response(
        client.post(
            "/api/signup/",
            json=user_data,
            headers={"X-Testing": "true"} if is_cross_site else None,
        ),
        expected_json={**user_data, "id": int, "password": None},
        expected_cookies={AUTH_COOKIE_NAME: str},
    )

    pochta_mock.assert_called_once()

    async with active_session():
        await assert_session_from_cookie(response, cross_site=is_cross_site)
        user = await User.find_first_by_id(response.json()["id"])
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
async def test_signing_up_conflict(
    client: TestClient,
    active_session: ActiveSession,
    user_data: dict[str, Any],
    user: User,
    is_cross_site: bool,
    data_mod: dict[str, Any],
    error: str,
) -> None:
    assert_response(
        client.post(
            "/api/signup/",
            json={**user_data, **data_mod},
            headers={"X-Testing": "true"} if is_cross_site else None,
        ),
        expected_code=409,
        expected_json={"detail": error},
        expected_headers={"Set-Cookie": None},
    )


@pytest.mark.anyio()
async def test_signing_in(
    client: TestClient,
    active_session: ActiveSession,
    user_data: dict[str, Any],
    user: User,
    is_cross_site: bool,
) -> None:
    response = assert_response(
        client.post(
            "/api/signin/",
            json=user_data,
            headers={"X-Testing": "true"} if is_cross_site else None,
        ),
        expected_json={**user_data, "id": user.id, "password": None},
        expected_cookies={AUTH_COOKIE_NAME: str},
    )

    async with active_session():
        await assert_session_from_cookie(response, cross_site=is_cross_site)


@pytest.mark.anyio()
@pytest.mark.usefixtures("user")
@pytest.mark.parametrize(
    ("altered_key", "error"),
    [
        pytest.param("email", "User not found", id="bad_email"),
        pytest.param("password", "Wrong password", id="wrong_password"),
    ],
)
async def test_signing_in_invalid_credentials(
    client: TestClient,
    user_data: dict[str, Any],
    altered_key: str,
    error: str,
) -> None:
    assert_response(
        client.post("/api/signin/", json={**user_data, altered_key: "alter"}),
        expected_code=401,
        expected_json={"detail": error},
        expected_headers={"Set-Cookie": None},
    )


@pytest.mark.anyio()
async def test_signing_out(
    authorized_client: TestClient,
    active_session: ActiveSession,
    session_token: str,
) -> None:
    assert_nodata_response(authorized_client.post("/api/signout"))

    async with active_session():
        await assert_session(session_token, invalid=True)


def test_signing_out_unauthorized(client: TestClient) -> None:
    assert_response(
        client.post("/api/signout/"),
        expected_code=401,
        expected_json={"detail": "Authorization is missing"},
    )


@pytest.mark.anyio()
async def test_signing_out_invalid_session(
    client: TestClient, invalid_token: str, use_cookie_auth: bool
) -> None:
    assert_response(
        client.post(
            "/api/signout/",
            cookies={AUTH_COOKIE_NAME: invalid_token} if use_cookie_auth else {},
            headers={} if use_cookie_auth else {AUTH_HEADER_NAME: invalid_token},
        ),
        expected_code=401,
        expected_json={"detail": "Session is invalid"},
    )
