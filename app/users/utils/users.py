from typing import Annotated

from fastapi import Depends, Path
from pydantic_marshals.base import PatchDefault, PatchDefaultType
from starlette.status import HTTP_404_NOT_FOUND, HTTP_409_CONFLICT

from app.common.fastapi_ext import Responses, with_responses
from app.users.models.users_db import User
from app.users.utils.magic import include_responses


class UsernameResponses(Responses):
    USERNAME_IN_USE = (HTTP_409_CONFLICT, "Username already in use")


async def is_username_unique(
    patch_username: str | PatchDefaultType, current_username: str | None = None
) -> bool:
    if patch_username is not PatchDefault and patch_username != current_username:
        return await User.find_first_by_kwargs(username=patch_username) is None
    return True


class UserEmailResponses(Responses):
    EMAIL_IN_USE = (HTTP_409_CONFLICT, "Email already in use")


async def is_email_unique(
    patch_email: str | PatchDefaultType, current_email: str | None = None
) -> bool:
    if patch_email is not PatchDefault and patch_email != current_email:
        return await User.find_first_by_kwargs(email=patch_email) is None
    return True


class UserResponses(Responses):
    USER_NOT_FOUND = (HTTP_404_NOT_FOUND, User.not_found_text)


@with_responses(UserResponses)
async def get_user_by_id(user_id: Annotated[int, Path()]) -> User:
    user = await User.find_first_by_id(user_id)
    if user is None:
        raise UserResponses.USER_NOT_FOUND.value
    return user


TargetUser = Annotated[User, Depends(get_user_by_id)]


@include_responses(UsernameResponses, UserEmailResponses)
class UserConflictResponses(Responses):
    pass
