from fastapi import APIRouter
from starlette.responses import Response

from app.utils.authorization import (
    AuthorizedResponses,
    AuthorizedSession,
    AuthorizedUser,
)

router = APIRouter(tags=["proxy auth"])


@router.get(
    "/",
    status_code=204,
    responses=AuthorizedResponses.responses(),
)
async def proxy_auth(
    session: AuthorizedSession, user: AuthorizedUser, response: Response
) -> None:
    response.headers["X-User-ID"] = str(user.id)
    response.headers["X-Session-ID"] = str(session.id)
