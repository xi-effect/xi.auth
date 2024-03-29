from datetime import datetime, timedelta
from typing import Any

import pytest
from starlette.testclient import TestClient

from app.models.sessions_db import Session
from app.models.users_db import User
from app.utils.authorization import AUTH_COOKIE_NAME, AUTH_HEADER_NAME
from tests.conftest import ActiveSession
from tests.utils import (
    PytestRequest,
    assert_nodata_response,
    assert_response,
    assert_session_from_cookie,
)


@pytest.mark.anyio()
async def test_retrieving_home_data(
    authorized_client: TestClient,
    user_data: dict[str, Any],
    user: User,
) -> None:
    assert_response(
        authorized_client.get("/api/users/current/home/"),
        expected_json={**user_data, "id": user.id, "password": None},
    )


@pytest.mark.anyio()
async def test_requesting_proxy_auth(
    authorized_client: TestClient,
    session: Session,
    user: User,
) -> None:
    assert_nodata_response(
        authorized_client.get("/proxy/auth/"),
        expected_headers={
            "X-User-ID": str(user.id),
            "X-Username": user.username,
            "X-Session-ID": str(session.id),
        },
    )


@pytest.mark.anyio()
async def test_requesting_options_in_proxy_auth(
    authorized_client: TestClient,
    session: Session,
    user: User,
) -> None:
    assert_nodata_response(
        authorized_client.get("/proxy/auth/", headers={"X-Request-Method": "OPTIONS"}),
        expected_headers={
            "X-User-ID": None,
            "X-Username": None,
            "X-Session-ID": None,
        },
    )


@pytest.mark.parametrize("cross_site", [False, True], ids=["same_site", "cross_site"])
@pytest.mark.anyio()
async def test_renewing_session_in_proxy_auth(
    active_session: ActiveSession,
    authorized_client: TestClient,
    session: Session,
    user: User,
    cross_site: bool,
) -> None:
    async with active_session() as db_session:
        session.expiry = datetime.utcnow() + timedelta(hours=3)
        session.cross_site = cross_site
        db_session.add(session)

    response = assert_nodata_response(
        authorized_client.get("/proxy/auth/"),
        expected_cookies={AUTH_COOKIE_NAME: str},
        expected_headers={
            "X-User-ID": str(user.id),
            "X-Username": user.username,
            "X-Session-ID": str(session.id),
        },
    )

    async with active_session():
        session_from_cookie = await assert_session_from_cookie(response, cross_site)
        assert session_from_cookie.id == session.id


@pytest.fixture(
    params=["/api/users/current/home/", "/proxy/auth/"],
    ids=["home", "proxy_auth"],
)
def path(request: PytestRequest[str]) -> str:
    return request.param


@pytest.mark.anyio()
async def test_requesting_unauthorized(client: TestClient, path: str) -> None:
    assert_response(
        client.get(path),
        expected_code=401,
        expected_json={"detail": "Authorization is missing"},
    )


@pytest.mark.anyio()
async def test_requesting_invalid_session(
    client: TestClient, invalid_token: str, path: str, use_cookie_auth: bool
) -> None:
    cookies = {AUTH_COOKIE_NAME: invalid_token} if use_cookie_auth else {}
    headers = {} if use_cookie_auth else {AUTH_HEADER_NAME: invalid_token}
    assert_response(
        client.get(path, cookies=cookies, headers=headers),
        expected_code=401,
        expected_json={"detail": "Session is invalid"},
    )
