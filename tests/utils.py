from http.cookiejar import Cookie
from typing import Generic, TypeVar

import pytest
from httpx import Response
from pydantic_marshals.contains import TypeChecker, assert_contains

from app.common.config import COOKIE_DOMAIN
from app.models.sessions_db import Session
from app.models.users_db import User
from app.utils.authorization import AUTH_COOKIE_NAME


def assert_nodata_response(
    response: Response,
    *,
    expected_code: int = 204,
    expected_headers: dict[str, TypeChecker] | None = None,
    expected_cookies: dict[str, TypeChecker] | None = None,
) -> Response:
    assert_contains(
        {
            "status_code": response.status_code,
            "headers": response.headers,
            "cookies": response.cookies,
        },
        {
            "status_code": expected_code,
            "headers": expected_headers or {},
            "cookies": expected_cookies or {},
        },
    )
    return response


def assert_response(
    response: Response,
    *,
    expected_code: int = 200,
    expected_json: TypeChecker,
    expected_headers: dict[str, TypeChecker] | None = None,
    expected_cookies: dict[str, TypeChecker] | None = None,
) -> Response:
    expected_headers = expected_headers or {}
    expected_headers["Content-Type"] = "application/json"
    assert_contains(
        {
            "status_code": response.status_code,
            "json_data": (
                response.json()
                if response.headers.get("Content-Type") == "application/json"
                else None
            ),
            "headers": response.headers,
            "cookies": response.cookies,
        },
        {
            "status_code": expected_code,
            "json_data": expected_json,
            "headers": expected_headers,
            "cookies": expected_cookies or {},
        },
    )
    return response


T = TypeVar("T")


class PytestRequest(Generic[T]):
    @property
    def param(self) -> T:
        raise NotImplementedError


async def get_db_user(user: User) -> User:
    db_user = await User.find_first_by_id(user.id)
    assert db_user is not None
    return db_user


async def get_db_session(session: Session) -> Session:
    db_session = await Session.find_first_by_id(session.id)
    assert db_session is not None
    return db_session


async def assert_session(token: str, invalid: bool = False) -> Session:
    session = await Session.find_first_by_kwargs(token=token)
    assert session is not None
    assert session.invalid == invalid
    return session


def find_auth_cookie(response: Response) -> Cookie:
    for cookie in response.cookies.jar:
        if cookie.name == AUTH_COOKIE_NAME:
            return cookie
    pytest.fail(f"{AUTH_COOKIE_NAME} not found in response")


async def assert_session_from_cookie(
    response: Response, cross_site: bool = False
) -> Session:
    cookie: Cookie = find_auth_cookie(response)

    assert_contains(
        {
            "value": cookie.value,
            "expired": cookie.is_expired(),
            "secure": cookie.secure,
            "domain": cookie.domain,
            "path": cookie.path,
            "httponly": cookie.has_nonstandard_attr("HttpOnly"),
            "same_site": cookie.get_nonstandard_attr("SameSite", "none"),
        },
        {
            "value": str,
            "expired": False,
            "secure": True,
            "domain": f".{COOKIE_DOMAIN}",
            "path": "/",
            "httponly": True,
            "same_site": "none" if cross_site else "strict",
        },
    )
    assert cookie.value is not None  # for mypy
    assert isinstance(cookie.expires, int)  # for mypy

    session = await assert_session(cookie.value)
    assert_contains(
        {"cross_site": cross_site, "expiry": cookie.expires},
        {"cross_site": session.cross_site, "expiry": int(session.expiry.timestamp())},
    )
    return session
