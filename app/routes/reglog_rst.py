from fastapi import APIRouter
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_409_CONFLICT

from app.common.responses import Responses
from app.models.users_db import User, UserPasswordModel

router = APIRouter(tags=["reglog"])


class SignupResponses(Responses):
    EMAIL_IN_USE = (HTTP_409_CONFLICT, "Email already in use")


@router.post(
    "/signup",
    response_model=User.FullModel,
    responses=SignupResponses.responses(),
)
async def signup(user_data: UserPasswordModel) -> User:
    if await User.find_first_by_kwargs(email=user_data.email) is not None:
        raise SignupResponses.EMAIL_IN_USE.value

    # TODO send email
    # TODO create token & add as headers
    return await User.create(**user_data.model_dump())


class SigninResponses(Responses):
    USER_NOT_FOUND = (HTTP_401_UNAUTHORIZED, User.not_found_text)
    WRONG_PASSWORD = (HTTP_401_UNAUTHORIZED, "Wrong password")


@router.post(
    "/signin",
    response_model=User.FullModel,
    responses=SigninResponses.responses(),
)
async def signin(user_data: User.InputModel) -> User:
    user = await User.find_first_by_kwargs(email=user_data.email)
    if user is None:
        raise SigninResponses.USER_NOT_FOUND.value

    if not user.is_password_valid(user_data.password):
        raise SigninResponses.WRONG_PASSWORD.value

    # TODO create token & add as headers
    return user
