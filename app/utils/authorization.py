from collections.abc import AsyncIterator
from typing import Annotated, Final

from fastapi import Depends, Response
from fastapi.security import APIKeyHeader
from starlette.status import HTTP_401_UNAUTHORIZED

from app.common.responses import Responses
from app.models.sessions_db import Session
from app.models.users_db import User

AUTH_HEADER: Final[str] = "X-XI-ID"
xi_id_scheme = APIKeyHeader(
    name=AUTH_HEADER.lower(),
    scheme_name="xi.id",
    auto_error=False,
)


class AuthorizedResponses(Responses):
    HEADER_MISSING = (HTTP_401_UNAUTHORIZED, "X-XI-ID header is missing")
    INVALID_SESSION = (HTTP_401_UNAUTHORIZED, "Session is invalid")


async def authorize_session(
    x_xi_id: Annotated[str | None, Depends(xi_id_scheme)]
) -> Session:
    if x_xi_id is None:
        raise AuthorizedResponses.HEADER_MISSING.value

    session = await Session.find_first_by_kwargs(token=x_xi_id)
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
        response.headers[AUTH_HEADER] = session.token


AuthorizedUser = Annotated[User, Depends(authorize_user)]
