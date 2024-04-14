from app.common.fastapi_extension import APIRouterExt
from app.models.users_db import User
from app.utils.users import (
    TargetUser,
    UserConflictResponses,
    UserEmailResponses,
    UsernameResponses,
    is_email_unique,
    is_username_unique,
)

router = APIRouterExt(tags=["users mub"])


@router.post(
    "/",
    response_model=User.FullModel,
    responses=UserConflictResponses.responses(),
    summary="Create a new user",
)
async def create_user(user_data: User.InputModel) -> User:
    if not await is_email_unique(user_data.email):
        raise UserEmailResponses.EMAIL_IN_USE.value
    if not await is_username_unique(user_data.username):
        raise UsernameResponses.USERNAME_IN_USE.value
    return await User.create(**user_data.model_dump())


@router.get(
    "/{user_id}/",
    response_model=User.FullModel,
    summary="Retrieve any user by id",
)
async def retrieve_user(user: TargetUser) -> User:
    return user


@router.patch(
    "/{user_id}/",
    response_model=User.FullModel,
    responses=UserConflictResponses.responses(),
    summary="Update any user's data by id",
)
async def update_user(user: TargetUser, user_data: User.FullPatchModel) -> User:
    if not await is_email_unique(user_data.email, user.email):
        raise UserEmailResponses.EMAIL_IN_USE.value
    if not await is_username_unique(user_data.username, user.username):
        raise UsernameResponses.USERNAME_IN_USE.value
    user.update(**user_data.model_dump(exclude_defaults=True))
    return user


@router.delete("/{user_id}/", status_code=204, summary="Delete any user by id")
async def delete_user(user: TargetUser) -> None:
    await user.delete()
