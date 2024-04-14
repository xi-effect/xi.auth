from typing import Annotated

from aio_pika import Message
from pydantic import Field
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_409_CONFLICT

from app.common.config import email_confirmation_cryptography, pochta_producer
from app.common.fastapi_extension import APIRouterExt, Responses
from app.models.users_db import User
from app.utils.authorization import AuthorizedSession, AuthorizedUser
from app.utils.magic import include_responses
from app.utils.users import (
    UserEmailResponses,
    UsernameResponses,
    is_email_unique,
    is_username_unique,
)

router = APIRouterExt(tags=["current user"])


@router.get(
    "/home/",
    response_model=User.FullModel,
    summary="Retrieve current user's profile data",
)
async def get_user_data(user: AuthorizedUser) -> User:
    return user


@router.patch(
    "/profile/",
    response_model=User.FullModel,
    responses=UsernameResponses.responses(),
    summary="Update current user's profile data",
)
async def patch_user_data(
    patch_data: User.ProfilePatchModel, user: AuthorizedUser
) -> User:
    if not await is_username_unique(patch_data.username, user.username):
        raise UsernameResponses.USERNAME_IN_USE.value
    user.update(**patch_data.model_dump(exclude_defaults=True))
    return user


class PasswordProtectedResponses(Responses):
    WRONG_PASSWORD = (HTTP_401_UNAUTHORIZED, "Wrong password")


class EmailChangeModel(User.PasswordModel):
    new_email: Annotated[str, Field(max_length=100)]


class PasswordChangeModel(User.PasswordModel):
    new_password: User.PasswordType


@include_responses(PasswordProtectedResponses, UserEmailResponses)
class EmailChangeResponses(Responses):
    pass


@router.put(
    "/email/",
    response_model=User.FullModel,
    responses=EmailChangeResponses.responses(),
    summary="Update current user's email",
)
async def change_user_email(user: AuthorizedUser, put_data: EmailChangeModel) -> User:
    if not user.is_password_valid(password=put_data.password):
        raise PasswordProtectedResponses.WRONG_PASSWORD.value

    if not await is_email_unique(put_data.new_email, user.username):
        raise UserEmailResponses.EMAIL_IN_USE.value

    user.email = put_data.new_email
    user.email_confirmed = False

    confirmation_token: str = email_confirmation_cryptography.encrypt(user.email)
    await pochta_producer.send_message(
        message=Message(
            (
                f"Your email has been changed to {put_data.new_email},"
                + f"confirm new email: {confirmation_token}"
            ).encode("utf-8")
        ),
    )

    return user


class PasswordChangeModel(User.PasswordModel):
    new_password: Annotated[str, Field(min_length=6, max_length=100)]


@include_responses(PasswordProtectedResponses)
class PasswordChangeResponse(Responses):
    PASSWORD_MATCHES_CURRENT = (
        HTTP_409_CONFLICT,
        "New password matches the current one",
    )


@router.put(
    "/password/",
    response_model=User.FullModel,
    responses=PasswordChangeResponse.responses(),
    summary="Update current user's password",
)
async def change_user_password(
    user: AuthorizedUser, session: AuthorizedSession, put_data: PasswordChangeModel
) -> User:
    if not user.is_password_valid(password=put_data.password):
        raise PasswordProtectedResponses.WRONG_PASSWORD

    if user.is_password_valid(put_data.new_password):
        raise PasswordChangeResponse.PASSWORD_MATCHES_CURRENT

    user.change_password(put_data.new_password)
    await session.disable_all_other()

    return user
