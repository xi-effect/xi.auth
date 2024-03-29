from typing import Annotated

from aio_pika import Message
from fastapi import APIRouter
from pydantic import Field
from starlette.status import HTTP_401_UNAUTHORIZED

from app.common.config import pochta_producer
from app.common.responses import Responses
from app.models.users_db import User
from app.utils.authorization import (
    AuthorizedResponses,
    AuthorizedSession,
    AuthorizedUser,
)
from app.utils.magic import include_responses
from app.utils.users import UsernameResponses, is_username_unique

router = APIRouter(tags=["current user"])


@router.get(
    "/home/",
    response_model=User.FullModel,
    responses=AuthorizedResponses.responses(),
)
async def get_user_data(user: AuthorizedUser) -> User:
    return user


@include_responses(UsernameResponses, AuthorizedResponses)
class UserPatchResponses(Responses):
    pass


@router.patch(
    "/profile/",
    response_model=User.FullModel,
    responses=UserPatchResponses.responses(),
    summary="Update current user's profile data",
)
async def patch_user_data(
    patch_data: User.ProfilePatchModel, user: AuthorizedUser
) -> User:
    if not await is_username_unique(patch_data.username, user.username):
        raise UsernameResponses.USERNAME_IN_USE.value
    user.update(**patch_data.model_dump(exclude_defaults=True))
    return user


@include_responses(AuthorizedResponses)
class PasswordProtectedResponses(Responses):
    WRONG_PASSWORD = (HTTP_401_UNAUTHORIZED, "Wrong password")


class EmailChangeModel(User.PasswordModel):
    new_email: Annotated[str, Field(max_length=100)]


class PasswordChangeModel(User.PasswordModel):
    new_password: User.PasswordType


@router.put(
    "/email/",
    response_model=User.FullModel,
    responses=PasswordProtectedResponses.responses(),
    summary="Update current user's email",
)
async def change_user_email(user: AuthorizedUser, put_data: EmailChangeModel) -> User:
    if not user.is_password_valid(password=put_data.password):
        raise PasswordProtectedResponses.WRONG_PASSWORD.value

    user.email = put_data.new_email
    await pochta_producer.send_message(
        message=Message(
            f"Your email has been changed to {put_data.new_email}".encode("utf-8")
        ),
    )

    return user


@router.put(
    "/password/",
    response_model=User.FullModel,
    responses=PasswordProtectedResponses.responses(),
    summary="Update current user's password",
)
async def change_user_password(
    user: AuthorizedUser, session: AuthorizedSession, put_data: PasswordChangeModel
) -> User:
    if not user.is_password_valid(password=put_data.password):
        raise PasswordProtectedResponses.WRONG_PASSWORD.value

    user.password = put_data.new_password
    await session.disable_all_other()

    return user
