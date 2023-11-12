from datetime import timezone
from email.utils import format_datetime
from typing import Any

import httpx
import pytest
from pydantic import constr
from pydantic_marshals.contains import UnorderedLiteralCollection, assert_contains
from starlette import responses
from starlette.testclient import TestClient

from app.common.config import COOKIE_DOMAIN
from app.models.sessions_db import Session
from app.models.users_db import User
from app.utils.authorization import AUTH_COOKIE, AUTH_HEADER
from tests.conftest import ActiveSession
from tests.utils import PytestRequest, assert_nodata_response, assert_response


async def assert_session(token: str, invalid: bool = False) -> Session:
    session = await Session.find_first_by_kwargs(token=token)
    assert session is not None
    assert session.invalid == invalid
    return session


async def assert_session_cookie(
    response: httpx.Response | responses.Response, cross_site: bool = False
) -> None:
    cookie_parts: list[str] = [
        part.strip()
        for part in response.headers["Set-Cookie"].partition("=")[2].split(";")
    ]

    session = await assert_session(cookie_parts[0])
    assert session.cross_site == cross_site

    expires = format_datetime(session.expiry.astimezone(timezone.utc), usegmt=True)
    assert_contains(
        [part.lower() for part in cookie_parts[1:]],
        UnorderedLiteralCollection(
            {
                f"domain={COOKIE_DOMAIN}",
                f"expires={expires.lower()}",
                "samesite=none" if cross_site else "samesite=strict",
                "path=/",
                "httponly",
                "secure",
            }
        ),
    )


COOKIE_REGEX = f"{AUTH_COOKIE}=(.*)"


@pytest.fixture(params=[False, True], ids=["same_site", "cross_site"])
def is_cross_site(request: PytestRequest[bool]) -> bool:
    return request.param


@pytest.mark.anyio()
async def test_signup(
    client: TestClient,
    active_session: ActiveSession,
    user_data: dict[str, Any],
    is_cross_site: bool,
) -> None:
    headers = {"X-Testing": "true"} if is_cross_site else {}
    response = assert_response(
        client.post("/api/signup", json=user_data, headers=headers),
        expected_json={**user_data, "id": int, "password": None},
        expected_headers={"Set-Cookie": constr(pattern=COOKIE_REGEX)},
    )

    async with active_session():
        await assert_session_cookie(response, cross_site=is_cross_site)

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
async def test_signup_conflict(
    client: TestClient,
    active_session: ActiveSession,
    user_data: dict[str, Any],
    user: User,
    is_cross_site: bool,
    data_mod: dict[str, Any],
    error: str,
) -> None:
    headers = {"X-Testing": "true"} if is_cross_site else {}
    assert_response(
        client.post("/api/signup", json={**user_data, **data_mod}, headers=headers),
        expected_code=409,
        expected_json={"detail": error},
        expected_headers={"Set-Cookie": None},
    )


@pytest.mark.anyio()
async def test_signin(
    client: TestClient,
    active_session: ActiveSession,
    user_data: dict[str, Any],
    user: User,
    is_cross_site: bool,
) -> None:
    headers = {"X-Testing": "true"} if is_cross_site else {}
    response = assert_response(
        client.post("/api/signin", json=user_data, headers=headers),
        expected_json={**user_data, "id": user.id, "password": None},
        expected_headers={"Set-Cookie": constr(pattern=COOKIE_REGEX)},
    )

    async with active_session():
        await assert_session_cookie(response, cross_site=is_cross_site)


@pytest.mark.usefixtures("user")
@pytest.mark.parametrize(
    ("altered_key", "error"),
    [
        pytest.param("email", "User not found", id="bad_email"),
        pytest.param("password", "Wrong password", id="wrong_password"),
    ],
)
def test_signin_errors(
    client: TestClient,
    user_data: dict[str, Any],
    altered_key: str,
    error: str,
) -> None:
    assert_response(
        client.post("/api/signin", json={**user_data, altered_key: "alter"}),
        expected_code=401,
        expected_json={"detail": error},
        expected_headers={"Set-Cookie": None},
    )


@pytest.mark.anyio()
async def test_signout(
    authorized_client: TestClient,
    active_session: ActiveSession,
    session_token: str,
) -> None:
    assert_nodata_response(authorized_client.post("/api/signout"))

    async with active_session():
        await assert_session(session_token, invalid=True)


def test_no_auth_header(client: TestClient) -> None:
    assert_response(
        client.post("/api/signout"),
        expected_code=401,
        expected_json={"detail": "Authorization cookie is missing"},
    )


def test_invalid_session(
    client: TestClient, invalid_token: str, use_cookie_auth: bool
) -> None:
    cookies = {AUTH_COOKIE: invalid_token} if use_cookie_auth else {}
    headers = {} if use_cookie_auth else {AUTH_HEADER: invalid_token}
    assert_response(
        client.post("/api/signout", cookies=cookies, headers=headers),
        expected_code=401,
        expected_json={"detail": "Session is invalid"},
    )
