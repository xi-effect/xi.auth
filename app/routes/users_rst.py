from fastapi import APIRouter

from app.common.responses import Responses
from app.models.users_db import User
from app.routes.users_mub import UserResponses
from app.utils.authorization import AuthorizedResponses, AuthorizedUser
from app.utils.magic import include_responses

router = APIRouter(tags=["users"])


@include_responses(UserResponses, AuthorizedResponses)
class UserProfileResponses(Responses):
    pass


@router.get(
    "/by_id/{user_id}/profile/",
    response_model=User.UserProfileModel,
    responses=UserProfileResponses.responses(),
    summary="Retrieve user profile by id",
)
async def get_profile_by_id(
    user_id: int,
    current_user: AuthorizedUser,
) -> User:
    user = await User.find_first_by_id(user_id)
    if user is None:
        raise UserResponses.USER_NOT_FOUND.value
    return user


@router.get(
    "/by_username/{username}/profile/",
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
