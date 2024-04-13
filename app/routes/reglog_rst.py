from aio_pika import Message
from fastapi import Response
from starlette.status import HTTP_401_UNAUTHORIZED

from app.common.config import email_confirmation_cryptography, pochta_producer
from app.common.fastapi_extension import APIRouterExt, Responses
from app.models.sessions_db import Session
from app.models.users_db import User
from app.utils.authorization import (
    AuthorizedSession,
    CrossSiteMode,
    add_session_to_response,
    remove_session_from_response,
)
from app.utils.users import UsernameResponses, UserCreationResponses, is_username_unique

router = APIRouterExt(tags=["reglog"])


@router.post(
    "/signup/",
    response_model=User.FullModel,
    responses=UserCreationResponses.responses(),
    summary="Register a new account",
)
async def signup(
    user_data: User.InputModel, cross_site: CrossSiteMode, response: Response
) -> User:
    if await User.find_first_by_kwargs(email=user_data.email) is not None:
        raise UserCreationResponses.EMAIL_IN_USE.value
    if await User.find_first_by_kwargs(username=user_data.username) is not None:
        raise UsernameResponses.USERNAME_IN_USE.value

    user = await User.create(**user_data.model_dump())

    confirmation_token: str = email_confirmation_cryptography.encrypt(user.email)
    await pochta_producer.send_message(
        message=Message(
            f"hi {user_data.email}, verify email: {confirmation_token}".encode("utf-8")
        ),
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
    summary="Sign in into an existing account (creates a new session)",
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


@router.post(
    "/signout/",
    status_code=204,
    summary="Sign out from current account (disables the current session and removes cookies)",
)
async def signout(session: AuthorizedSession, response: Response) -> None:
    session.disabled = True
    remove_session_from_response(response)
