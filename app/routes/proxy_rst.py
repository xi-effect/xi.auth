from typing import Annotated

from fastapi import APIRouter, Header
from starlette.responses import Response

from app.utils.authorization import (
    AuthCookie,
    AuthHeader,
    authorize_session,
    authorize_user,
)

router = APIRouter(tags=["proxy auth"])


@router.get(
    "/",
    status_code=204,
)
async def proxy_auth(
    response: Response,
    x_request_method: Annotated[str | None, Header(alias="X-Request-Method")] = None,
    header_token: AuthHeader = None,
    cookie_token: AuthCookie = None,
) -> None:
    if x_request_method and x_request_method.upper() == "OPTIONS":
        return

    session = await authorize_session(
        header_token=header_token, cookie_token=cookie_token
    )
    user = await authorize_user(session, response)

    response.headers["X-Session-ID"] = str(session.id)
    response.headers["X-User-ID"] = str(user.id)
    response.headers["X-Username"] = user.username
