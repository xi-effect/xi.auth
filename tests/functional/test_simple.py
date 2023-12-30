from datetime import datetime, timedelta
from typing import Any

import pytest
from pydantic import constr
from starlette.testclient import TestClient

from app.models.sessions_db import Session
from app.models.users_db import User
from app.utils.authorization import AUTH_COOKIE_NAME, AUTH_HEADER_NAME
from tests.conftest import ActiveSession
from tests.functional.test_reglog import COOKIE_REGEX, assert_session_cookie
from tests.utils import PytestRequest, assert_nodata_response, assert_response


@pytest.mark.anyio()
async def test_home_success(
    authorized_client: TestClient,
    user_data: dict[str, Any],
    user: User,
) -> None:
    assert_response(
        authorized_client.get("/api/users/current/home/"),
        expected_json={**user_data, "id": user.id, "password": None},
    )


@pytest.mark.anyio()
async def test_proxy_auth_success(
    authorized_client: TestClient,
    session: Session,
    user: User,
) -> None:
    assert_nodata_response(
        authorized_client.get("/proxy/auth/"),
        expected_headers={
            "X-User-ID": str(user.id),
            "X-Username": str(user.username),
            "X-Session-ID": str(session.id),
        },
    )


@pytest.mark.anyio()
async def test_proxy_auth_success_for_optional(
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
async def test_proxy_auth_renewal(
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
        expected_headers={
            "X-User-ID": str(user.id),
            "X-Username": str(user.username),
            "X-Session-ID": str(session.id),
            "Set-Cookie": constr(pattern=COOKIE_REGEX),
        },
    )
    await assert_session_cookie(response, cross_site)


@pytest.fixture(
    params=["/api/users/current/home/", "/proxy/auth/"],
    ids=["home", "proxy_auth"],
)
def path(request: PytestRequest[str]) -> str:
    return request.param


@pytest.mark.anyio()
async def test_no_auth_header(client: TestClient, path: str) -> None:
    assert_response(
        client.get(path),
        expected_code=401,
        expected_json={"detail": "Authorization is missing"},
    )


@pytest.mark.anyio()
async def test_invalid_session(
    client: TestClient, invalid_token: str, path: str, use_cookie_auth: bool
) -> None:
    cookies = {AUTH_COOKIE_NAME: invalid_token} if use_cookie_auth else {}
    headers = {} if use_cookie_auth else {AUTH_HEADER_NAME: invalid_token}
    assert_response(
        client.get(path, cookies=cookies, headers=headers),
        expected_code=401,
        expected_json={"detail": "Session is invalid"},
    )
