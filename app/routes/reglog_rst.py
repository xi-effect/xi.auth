from aio_pika import Message
from fastapi import APIRouter, Response
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_409_CONFLICT

from app.common.config import pochta_producer
from app.common.responses import Responses
from app.models.sessions_db import Session
from app.models.users_db import User
from app.utils.authorization import (
    AuthorizedResponses,
    AuthorizedSession,
    CrossSiteMode,
    add_session_to_response,
    remove_session_from_response,
)

router = APIRouter(tags=["reglog"])


class SignupResponses(Responses):
    EMAIL_IN_USE = (HTTP_409_CONFLICT, "Email already in use")
    USERNAME_IN_USE = (HTTP_409_CONFLICT, "Username already in use")


@router.post(
    "/signup/",
    response_model=User.FullModel,
    responses=SignupResponses.responses(),
)
async def signup(
    user_data: User.InputModel, cross_site: CrossSiteMode, response: Response
) -> User:
    if await User.find_first_by_kwargs(email=user_data.email) is not None:
        raise SignupResponses.EMAIL_IN_USE.value
    if await User.find_first_by_kwargs(username=user_data.username) is not None:
        raise SignupResponses.USERNAME_IN_USE.value

    user = await User.create(**user_data.model_dump())

    await pochta_producer.send_message(
        message=Message(f"hi {user_data.email}".encode("utf-8")),
    )

    session = await Session.create(user=user, cross_site=cross_site)
    add_session_to_response(response, session)

    return user


class SigninResponses(Responses):
    USER_NOT_FOUND = (HTTP_401_UNAUTHORIZED, User.not_found_text)
    WRONG_PASSWORD = (HTTP_401_UNAUTHORIZED, "Wrong password")


@router.post(
    "/signin/",
    response_model=User.FullModel,
    responses=SigninResponses.responses(),
)
async def signin(
    user_data: User.CredentialsModel, cross_site: CrossSiteMode, response: Response
) -> User:
    user = await User.find_first_by_kwargs(email=user_data.email)
    if user is None:
        raise SigninResponses.USER_NOT_FOUND.value

    if not user.is_password_valid(user_data.password):
        raise SigninResponses.WRONG_PASSWORD.value

    session = await Session.create(user=user, cross_site=cross_site)
    add_session_to_response(response, session)
    await Session.cleanup_by_user(user.id)

    return user


@router.post("/signout/", responses=AuthorizedResponses.responses(), status_code=204)
async def signout(session: AuthorizedSession, response: Response) -> None:
    session.disabled = True
    remove_session_from_response(response)
