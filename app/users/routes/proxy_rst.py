from contextlib import suppress
from typing import Annotated

from fastapi import Header, HTTPException
from starlette.responses import Response

from app.common.fastapi_ext import APIRouterExt
from app.users.utils.authorization import (
    AuthCookie,
    AuthHeader,
    authorize_session,
    authorize_user,
)

router = APIRouterExt(tags=["proxy auth"])


@router.get(
    "/proxy/auth/",
    status_code=204,
    summary="Retrieve headers for proxy authorization, return 401 on invalid auth",
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


@router.get(
    "/proxy/optional-auth/",
    status_code=204,
    summary="Retrieve headers for proxy authorization, do nothing on invalid auth",
)
async def optional_proxy_auth(
    response: Response,
    x_request_method: Annotated[str | None, Header(alias="X-Request-Method")] = None,
    header_token: AuthHeader = None,
    cookie_token: AuthCookie = None,
) -> None:
    with suppress(HTTPException):
        await proxy_auth(
            response=response,
            x_request_method=x_request_method,
            header_token=header_token,
            cookie_token=cookie_token,
        )
