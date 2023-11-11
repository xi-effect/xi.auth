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
TEST_HEADER: Final[str] = "X-Testing"
AUTH_COOKIE: Final[str] = "xi_id_token"


def add_session_to_response(response: Response, session: Session) -> None:
    response.set_cookie(
        AUTH_COOKIE,
        session.token,
        expires=session.expiry.astimezone(timezone.utc),
        domain=COOKIE_DOMAIN,
        samesite="none" if session.cross_site else "strict",
        httponly=True,
        secure=True,
    )


def remove_session_from_response(response: Response) -> None:
    response.delete_cookie(AUTH_COOKIE, domain=COOKIE_DOMAIN)


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


def is_cross_site_mode(testing: Annotated[str, Header(alias=TEST_HEADER)] = "") -> bool:
    return testing == "true"


CrossSiteMode = Annotated[bool, Depends(is_cross_site_mode)]


async def authorize_user(
    session: AuthorizedSession,
    response: Response,
) -> User:
    if session.is_renewal_required():
        session.renew()
        add_session_to_response(response, session)

    return await session.awaitable_attrs.user  # type: ignore[no-any-return]


AuthorizedUser = Annotated[User, Depends(authorize_user)]
