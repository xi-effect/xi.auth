from fastapi import APIRouter

from app.common.responses import Responses
from app.models.users_db import User
from app.routes.reglog_rst import SignupResponses
from app.utils.magic import include_responses
from app.utils.mub import MUBResponses
from app.utils.users import (
    TargetUser,
    UsernameResponses,
    UserResponses,
    is_username_unique,
)

router = APIRouter(tags=["users mub"])


@include_responses(SignupResponses, MUBResponses)
class MUBUserCreateResponses(Responses):
    pass


@router.post(
    "/", response_model=User.FullModel, responses=MUBUserCreateResponses.responses()
)
async def create_user(user_data: User.InputModel) -> User:
    if await User.find_first_by_kwargs(email=user_data.email) is not None:
        raise SignupResponses.EMAIL_IN_USE.value
    if await User.find_first_by_kwargs(username=user_data.username) is not None:
        raise UsernameResponses.USERNAME_IN_USE.value
    return await User.create(**user_data.model_dump())


@include_responses(UserResponses, MUBResponses)
class MUBUserResponses(Responses):
    pass


@router.get(
    "/{user_id}/",
    response_model=User.FullModel,
    responses=MUBUserResponses.responses(),
)
async def retrieve_user(user: TargetUser) -> User:
    return user


@include_responses(UsernameResponses, UserResponses, MUBResponses)
class MUBUserUpdateResponses(Responses):
    pass


@router.patch(
    "/{user_id}/",
    response_model=User.FullModel,
    responses=MUBUserUpdateResponses.responses(),
    summary="Update user's data by id",
)
async def update_user(user: TargetUser, user_data: User.FullPatchModel) -> User:
    if not await is_username_unique(user_data.username, user.username):
        raise UsernameResponses.USERNAME_IN_USE.value
    user.update(**user_data.model_dump(exclude_defaults=True))
    return user


@router.delete(
    "/{user_id}/",
    status_code=204,
    responses=MUBUserResponses.responses(),
)
async def delete_user(user: TargetUser) -> None:
    await user.delete()
