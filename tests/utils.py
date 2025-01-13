from http.cookiejar import Cookie

import pytest
from httpx import Response
from pydantic_marshals.contains import assert_contains

from app.common.config import settings
from app.users.models.sessions_db import Session
from app.users.models.users_db import User
from app.users.utils.authorization import AUTH_COOKIE_NAME


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
            "domain": f".{settings.cookie_domain}",
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
