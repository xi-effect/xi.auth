from collections.abc import Sequence

from fastapi import APIRouter
from starlette.status import HTTP_404_NOT_FOUND

from app.common.responses import Responses, SuccessResponse
from app.models.sessions_db import Session
from app.utils.authorization import (
    AuthorizedResponses,
    AuthorizedSession,
    AuthorizedUser,
)
from app.utils.magic import include_responses

router = APIRouter(tags=["user sessions"])


@router.get(
    "/",
    response_model=list[Session.FullModel],
    responses=AuthorizedResponses.responses(),
)
async def list_sessions(user: AuthorizedUser) -> Sequence[Session]:
    return await Session.find_by_user(user.id)


@router.delete("/", responses=AuthorizedResponses.responses())
async def disable_all_but_current(session: AuthorizedSession) -> SuccessResponse:
    await session.disable_all_other()
    return SuccessResponse()


@include_responses(AuthorizedResponses)
class SessionResponses(Responses):
    SESSION_NOT_FOUND = (HTTP_404_NOT_FOUND, Session.not_found_text)


@router.delete("/{session_id}", responses=SessionResponses.responses())
async def disable_session(session_id: int, user: AuthorizedUser) -> SuccessResponse:
    session = await Session.find_first_by_kwargs(id=session_id, user_id=user.id)
    if session is None:
        raise SessionResponses.SESSION_NOT_FOUND.value
    session.disabled = True
    return SuccessResponse()
