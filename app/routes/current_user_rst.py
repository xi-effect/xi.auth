from fastapi import APIRouter

from app.common.responses import Responses
from app.models.users_db import User
from app.utils.authorization import AuthorizedResponses, AuthorizedUser
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
