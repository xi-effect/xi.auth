from collections.abc import Sequence

from starlette.status import HTTP_404_NOT_FOUND

from app.common.fastapi_ext import APIRouterExt, Responses
from app.users.models.sessions_db import Session
from app.users.utils.authorization import AuthorizedSession, AuthorizedUser

router = APIRouterExt(tags=["user sessions"])


@router.get(
    "/current/",
    response_model=Session.FullModel,
    summary="Retrieve current session's data",
)
async def get_current_session(session: AuthorizedSession) -> Session:
    return session


@router.get(
    "/",
    response_model=list[Session.FullModel],
    summary="List all current user's sessions but the current one",
)
async def list_sessions(
    user: AuthorizedUser, session: AuthorizedSession
) -> Sequence[Session]:
    return await Session.find_by_user(user.id, exclude_id=session.id)


@router.delete(
    "/",
    status_code=204,
    summary="Disable all current user's sessions but the current one",
)
async def disable_all_but_current(session: AuthorizedSession) -> None:
    await session.disable_all_other()


class SessionResponses(Responses):
    SESSION_NOT_FOUND = (HTTP_404_NOT_FOUND, Session.not_found_text)


@router.delete(
    "/{session_id}/",
    responses=SessionResponses.responses(),
    status_code=204,
    summary="Disable a specific user session",
)
async def disable_session(session_id: int, user: AuthorizedUser) -> None:
    session = await Session.find_first_by_kwargs(
        id=session_id,
        user_id=user.id,
        mub=False,
    )
    if session is None:
        raise SessionResponses.SESSION_NOT_FOUND.value
    session.disabled = True
