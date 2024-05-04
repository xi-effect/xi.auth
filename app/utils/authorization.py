from datetime import timezone
from typing import Annotated, Final

from fastapi import Depends, Response
from fastapi.params import Header
from fastapi.security import APIKeyCookie, APIKeyHeader
from starlette.status import HTTP_401_UNAUTHORIZED

from app.common.config import COOKIE_DOMAIN
from app.common.fastapi_extension import Responses, with_responses
from app.models.sessions_db import Session
from app.models.users_db import User

AUTH_HEADER_NAME: Final[str] = "X-XI-ID"
AUTH_COOKIE_NAME: Final[str] = "xi_id_token"
TEST_HEADER_NAME: Final[str] = "X-Testing"

header_auth_scheme = APIKeyHeader(
    name=AUTH_HEADER_NAME, auto_error=False, scheme_name="auth header"
)
AuthHeader = Annotated[str | None, Depends(header_auth_scheme)]

cookie_auth_scheme = APIKeyCookie(
    name=AUTH_COOKIE_NAME, auto_error=False, scheme_name="auth cookie"
)
AuthCookie = Annotated[str | None, Depends(cookie_auth_scheme)]


def add_session_to_response(response: Response, session: Session) -> None:
    response.set_cookie(
        AUTH_COOKIE_NAME,
        session.token,
        expires=session.expiry.astimezone(timezone.utc),
        domain=COOKIE_DOMAIN,
        samesite="none" if session.cross_site else "strict",
        httponly=True,
        secure=True,
    )


def remove_session_from_response(response: Response) -> None:
    response.delete_cookie(AUTH_COOKIE_NAME, domain=COOKIE_DOMAIN)


class AuthorizedResponses(Responses):
    HEADER_MISSING = (HTTP_401_UNAUTHORIZED, "Authorization is missing")
    INVALID_SESSION = (HTTP_401_UNAUTHORIZED, "Session is invalid")


@with_responses(AuthorizedResponses)
async def authorize_session(
    header_token: AuthHeader = None,
    cookie_token: AuthCookie = None,
) -> Session:
    token = cookie_token or header_token
    if token is None:
        raise AuthorizedResponses.HEADER_MISSING.value

    session = await Session.find_first_by_kwargs(token=token)
    if session is None or session.invalid:
        raise AuthorizedResponses.INVALID_SESSION.value

    return session


AuthorizedSession = Annotated[Session, Depends(authorize_session)]


def is_cross_site_mode(
    testing: Annotated[str, Header(alias=TEST_HEADER_NAME)] = ""
) -> bool:
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
