from fastapi import APIRouter

from app.common.responses import Responses
from app.models.users_db import User
from app.utils.authorization import AuthorizedResponses, AuthorizedUser
from app.utils.magic import include_responses
from app.utils.users import TargetUser, UserResponses

router = APIRouter(tags=["users"])


@include_responses(UserResponses, AuthorizedResponses)
class UserProfileResponses(Responses):
    pass


@router.get(
    "/by-id/{user_id}/profile/",
    response_model=User.UserProfileModel,
    responses=UserProfileResponses.responses(),
    summary="Retrieve user profile by id",
)
async def get_profile_by_id(
    user: TargetUser,
    current_user: AuthorizedUser,
) -> User:
    return user


@router.get(
    "/by-username/{username}/profile/",
    response_model=User.UserProfileModel,
    responses=UserProfileResponses.responses(),
    summary="Retrieve user profile by username",
)
async def get_profile_by_username(
    username: str,
    current_user: AuthorizedUser,
) -> User:
    user = await User.find_first_by_kwargs(username=username)
    if user is None:
        raise UserResponses.USER_NOT_FOUND.value
    return user
