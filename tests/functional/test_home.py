from typing import Any

import pytest
from starlette.testclient import TestClient

from app.models.users_db import User
from app.utils.authorization import AUTH_COOKIE, AUTH_HEADER
from tests.utils import PytestRequest, assert_response


@pytest.fixture(
    params=["/api/users/current/home/", "/mub/sessions/current/user/"],
    ids=["api", "mub"],
)
def path(request: PytestRequest[str]) -> str:
    return request.param


@pytest.mark.anyio()
async def test_home_success(
    authorized_client: TestClient,
    user_data: dict[str, Any],
    user: User,
    path: str,
) -> None:
    assert_response(
        authorized_client.get(path),
        expected_json={**user_data, "id": user.id, "password": None},
    )


@pytest.mark.anyio()
async def test_home_no_auth_header(client: TestClient, path: str) -> None:
    assert_response(
        client.get(path),
        expected_code=401,
        expected_json={"detail": "Authorization cookie is missing"},
    )


@pytest.mark.anyio()
async def test_home_invalid_session(
    client: TestClient, invalid_token: str, path: str, use_cookie_auth: bool
) -> None:
    cookies = {AUTH_COOKIE: invalid_token} if use_cookie_auth else {}
    headers = {} if use_cookie_auth else {AUTH_HEADER: invalid_token}
    assert_response(
        client.get(path, cookies=cookies, headers=headers),
        expected_code=401,
        expected_json={"detail": "Session is invalid"},
    )
