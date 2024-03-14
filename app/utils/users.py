from typing import Annotated

from fastapi import Depends, Path
from pydantic_marshals.base import PatchDefault, PatchDefaultType
from starlette.status import HTTP_404_NOT_FOUND, HTTP_409_CONFLICT

from app.common.responses import Responses
from app.models.users_db import User


class UserResponses(Responses):
    USER_NOT_FOUND = (HTTP_404_NOT_FOUND, User.not_found_text)


class UsernameResponses(Responses):
    USERNAME_IN_USE = (HTTP_409_CONFLICT, "Username already in use")


async def is_username_unique(
    patch_username: str | PatchDefaultType, current_username: str
) -> bool:
    if patch_username is not PatchDefault and patch_username != current_username:
        return await User.find_first_by_kwargs(username=patch_username) is None
    return True


async def get_user_by_id(user_id: Annotated[int, Path()]) -> User:
    user = await User.find_first_by_id(user_id)
    if user is None:
        raise UserResponses.USER_NOT_FOUND.value
    return user


TargetUser = Annotated[User, Depends(get_user_by_id)]
