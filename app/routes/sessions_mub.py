from collections.abc import Sequence

from fastapi import APIRouter, Response
from starlette.status import HTTP_404_NOT_FOUND

from app.common.responses import Responses
from app.models.sessions_db import Session
from app.utils.authorization import add_session_to_response
from app.utils.magic import include_responses
from app.utils.users import TargetUser, UserResponses

router = APIRouter(tags=["sessions mub"])


@include_responses(UserResponses)
class MubSessionResponses(Responses):
    SESSION_NOT_FOUND = (HTTP_404_NOT_FOUND, Session.not_found_text)


@router.post(
    "/",
    status_code=204,
    responses=UserResponses.responses(),
    summary="Create a new admin session",
)
async def make_mub_session(
    response: Response,
    user: TargetUser,
) -> None:
    session = await Session.create(user_id=user.id, mub=True)
    add_session_to_response(response, session)


@router.put(
    "/",
    status_code=204,
    responses=MubSessionResponses.responses(),
    summary="Retrive or create an admin session",
)
async def upsert_mub_session(
    response: Response,
    user: TargetUser,
) -> None:
    session = await Session.find_active_mub_session(user.id)
    if session is None:
        session = await Session.create(user_id=user.id, mub=True)
    add_session_to_response(response, session)


@router.get(
    "/",
    response_model=list[Session.MubFullModel],
    responses=UserResponses.responses(),
    summary="Show all user sessions",
)
async def list_all_sessions(user: TargetUser) -> Sequence[Session]:
    return await Session.find_all_by_kwargs(Session.expiry.desc(), user_id=user.id)


@router.delete(
    "/{session_id}/",
    status_code=204,
    responses=MubSessionResponses.responses(),
    summary="Disable or delete any user session",
)
async def disable_or_delete_session(
    session_id: int,
    user: TargetUser,
    delete_session: bool = False,
) -> None:
    session = await Session.find_first_by_kwargs(id=session_id, user_id=user.id)
    if session is None:
        raise MubSessionResponses.SESSION_NOT_FOUND.value
    if delete_session:
        await session.delete()
    else:
        session.disabled = True
