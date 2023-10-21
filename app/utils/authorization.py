from collections.abc import AsyncIterator
from datetime import timezone
from typing import Annotated, Final

from fastapi import Depends, Response
from fastapi.params import Cookie, Header
from starlette.status import HTTP_401_UNAUTHORIZED

from app.common.config import COOKIE_DOMAIN
from app.common.responses import Responses
from app.models.sessions_db import Session
from app.models.users_db import User

AUTH_HEADER: Final[str] = "X-XI-ID"
AUTH_COOKIE: Final[str] = "xi_id_token"


def add_session_to_response(response: Response, session: Session) -> None:
    response.set_cookie(
        AUTH_COOKIE,
        session.token,
        expires=session.expiry.astimezone(timezone.utc),
        domain=COOKIE_DOMAIN,
        samesite="strict",
        httponly=True,
        secure=True,
    )


def remove_session_from_response(response: Response) -> None:
    response.delete_cookie(
        AUTH_COOKIE,
        domain=COOKIE_DOMAIN,
        samesite="strict",
        httponly=True,
        secure=True,
    )


class AuthorizedResponses(Responses):
    HEADER_MISSING = (HTTP_401_UNAUTHORIZED, "Authorization cookie is missing")
    INVALID_SESSION = (HTTP_401_UNAUTHORIZED, "Session is invalid")


async def authorize_session(
    header_token: Annotated[str | None, Header(alias=AUTH_HEADER)] = None,
    cookie_token: Annotated[str | None, Cookie(alias=AUTH_COOKIE)] = None,
) -> Session:
    token = cookie_token or header_token
    if token is None:
        raise AuthorizedResponses.HEADER_MISSING.value

    session = await Session.find_first_by_kwargs(token=token)
    if session is None or session.invalid:
        raise AuthorizedResponses.INVALID_SESSION.value

    return session


AuthorizedSession = Annotated[Session, Depends(authorize_session)]


async def authorize_user(
    session: AuthorizedSession,
    response: Response,
) -> AsyncIterator[User]:
    yield await session.awaitable_attrs.user

    if session.is_renewal_required():
        session.renew()
        add_session_to_response(response, session)


AuthorizedUser = Annotated[User, Depends(authorize_user)]
