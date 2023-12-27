from pydantic_marshals.base import PatchDefault, PatchDefaultType
from starlette.status import HTTP_409_CONFLICT

from app.common.responses import Responses
from app.models.users_db import User


class UsernameResponses(Responses):
    USERNAME_IN_USE = (HTTP_409_CONFLICT, "Username already in use")


async def is_username_unique(
    patch_username: str | PatchDefaultType, current_username: str
) -> bool:
    if patch_username is not PatchDefault and patch_username != current_username:
        return await User.find_first_by_kwargs(username=patch_username) is None
    return True
