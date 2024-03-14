from collections.abc import Sequence

from fastapi import APIRouter
from starlette.status import HTTP_404_NOT_FOUND

from app.common.responses import Responses
from app.models.sessions_db import Session
from app.utils.authorization import (
    AuthorizedResponses,
    AuthorizedSession,
    AuthorizedUser,
)
from app.utils.magic import include_responses

router = APIRouter(tags=["user sessions"])


@router.get(
    "/current/",
    response_model=Session.FullModel,
    responses=AuthorizedResponses.responses(),
)
async def get_current_session(session: AuthorizedSession) -> Session:
    return session


@router.get(
    "/",
    response_model=list[Session.FullModel],
    responses=AuthorizedResponses.responses(),
)
async def list_sessions(
    user: AuthorizedUser, session: AuthorizedSession
) -> Sequence[Session]:
    return await Session.find_by_user(user.id, exclude_id=session.id)


@router.delete("/", responses=AuthorizedResponses.responses(), status_code=204)
async def disable_all_but_current(session: AuthorizedSession) -> None:
    await session.disable_all_other()


@include_responses(AuthorizedResponses)
class SessionResponses(Responses):
    SESSION_NOT_FOUND = (HTTP_404_NOT_FOUND, Session.not_found_text)


@router.delete(
    "/{session_id}/", responses=SessionResponses.responses(), status_code=204
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
