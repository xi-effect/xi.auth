from collections.abc import Sequence

from fastapi import Response
from starlette.status import HTTP_404_NOT_FOUND

from app.common.fastapi_ext import APIRouterExt, Responses
from app.users.models.sessions_db import Session
from app.users.utils.authorization import AUTH_COOKIE_NAME, add_session_to_response
from app.users.utils.users import TargetUser

router = APIRouterExt(tags=["sessions mub"])


def add_mub_session_to_response(response: Response, session: Session) -> None:
    add_session_to_response(response, session)

    response.headers["X-Session-ID"] = str(session.id)
    response.headers["X-User-ID"] = str(session.user_id)
    response.headers["X-Username"] = session.user.username

    response.headers["X-Session-Cookie"] = AUTH_COOKIE_NAME
    response.headers["X-Session-Token"] = session.token


@router.post(
    "/",
    status_code=201,
    summary="Create a new admin session",
)
async def make_mub_session(response: Response, user: TargetUser) -> None:
    session = await Session.create(user_id=user.id, mub=True)
    add_mub_session_to_response(response, session)


@router.put(
    "/",
    status_code=204,
    summary="Retrieve or create an admin session",
)
async def upsert_mub_session(response: Response, user: TargetUser) -> None:
    session = await Session.find_active_mub_session(user.id)
    if session is None:
        session = await Session.create(user_id=user.id, mub=True)
    add_mub_session_to_response(response, session)


@router.get(
    "/",
    response_model=list[Session.MUBFullModel],
    summary="List all user sessions",
)
async def list_all_sessions(user: TargetUser) -> Sequence[Session]:
    return await Session.find_all_by_kwargs(Session.expiry.desc(), user_id=user.id)


class SessionResponses(Responses):
    SESSION_NOT_FOUND = (HTTP_404_NOT_FOUND, Session.not_found_text)


@router.delete(
    "/{session_id}/",
    status_code=204,
    responses=SessionResponses.responses(),
    summary="Disable or delete any user session",
)
async def disable_or_delete_session(
    session_id: int,
    user: TargetUser,
    delete_session: bool = False,
) -> None:
    session = await Session.find_first_by_kwargs(id=session_id, user_id=user.id)
    if session is None:
        raise SessionResponses.SESSION_NOT_FOUND.value
    if delete_session:
        await session.delete()
    else:
        session.disabled = True
