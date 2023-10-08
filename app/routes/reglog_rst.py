from fastapi import APIRouter, Response
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_409_CONFLICT

from app.common.responses import Responses
from app.models.sessions_db import Session
from app.models.users_db import User, UserPasswordModel
from app.utils.authorization import AUTH_HEADER, AuthorizedResponses, AuthorizedSession

router = APIRouter(tags=["reglog"])


class SignupResponses(Responses):
    EMAIL_IN_USE = (HTTP_409_CONFLICT, "Email already in use")


@router.post(
    "/signup",
    response_model=User.FullModel,
    responses=SignupResponses.responses(),
)
async def signup(user_data: UserPasswordModel, response: Response) -> User:
    if await User.find_first_by_kwargs(email=user_data.email) is not None:
        raise SignupResponses.EMAIL_IN_USE.value

    user = await User.create(**user_data.model_dump())

    # TODO send email

    session = await Session.create(user=user)
    response.headers[AUTH_HEADER] = session.token

    return user


class SigninResponses(Responses):
    USER_NOT_FOUND = (HTTP_401_UNAUTHORIZED, User.not_found_text)
    WRONG_PASSWORD = (HTTP_401_UNAUTHORIZED, "Wrong password")


@router.post(
    "/signin",
    response_model=User.FullModel,
    responses=SigninResponses.responses(),
)
async def signin(user_data: User.InputModel, response: Response) -> User:
    user = await User.find_first_by_kwargs(email=user_data.email)
    if user is None:
        raise SigninResponses.USER_NOT_FOUND.value

    if not user.is_password_valid(user_data.password):
        raise SigninResponses.WRONG_PASSWORD.value

    session = await Session.create(user=user)
    response.headers[AUTH_HEADER] = session.token
    await Session.cleanup_by_user(user.id)

    return user


@router.post("/signout", responses=AuthorizedResponses.responses(), status_code=204)
async def signout(session: AuthorizedSession) -> None:
    session.disabled = True
