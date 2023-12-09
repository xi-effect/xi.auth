from typing import Annotated

from fastapi import APIRouter, Cookie, Header
from starlette.responses import Response

from app.utils.authorization import (
    AUTH_COOKIE,
    AUTH_HEADER,
    AuthorizedResponses,
    authorize_session,
    authorize_user,
)

router = APIRouter(tags=["proxy auth"])


@router.get(
    "/",
    status_code=204,
    responses=AuthorizedResponses.responses(),
)
async def proxy_auth(
    response: Response,
    x_request_method: Annotated[str | None, Header(alias="X-Request-Method")] = None,
    header_token: Annotated[str | None, Header(alias=AUTH_HEADER)] = None,
    cookie_token: Annotated[str | None, Cookie(alias=AUTH_COOKIE)] = None,
) -> None:
    if x_request_method and x_request_method.upper() == "OPTIONS":
        return

    session = await authorize_session(
        header_token=header_token, cookie_token=cookie_token
    )
    user = await authorize_user(session, response)

    response.headers["X-Session-ID"] = str(session.id)
    response.headers["X-User-ID"] = str(user.id)
    response.headers["X-Username"] = str(user.username)
