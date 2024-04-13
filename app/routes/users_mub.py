from app.common.fastapi_extension import APIRouterExt
from app.models.users_db import User
from app.utils.users import (
    TargetUser,
    UserCreationResponses,
    UsernameResponses,
    is_username_unique,
)

router = APIRouterExt(tags=["users mub"])


@router.post(
    "/", response_model=User.FullModel, responses=UserCreationResponses.responses()
)
async def create_user(user_data: User.InputModel) -> User:
    if await User.find_first_by_kwargs(email=user_data.email) is not None:
        raise UserCreationResponses.EMAIL_IN_USE.value
    if await User.find_first_by_kwargs(username=user_data.username) is not None:
        raise UsernameResponses.USERNAME_IN_USE.value
    return await User.create(**user_data.model_dump())


@router.get(
    "/{user_id}/",
    response_model=User.FullModel,
)
async def retrieve_user(user: TargetUser) -> User:
    return user


@router.patch(
    "/{user_id}/",
    response_model=User.FullModel,
    responses=UsernameResponses.responses(),
    summary="Update any user's data by id",
)
async def update_user(user: TargetUser, user_data: User.FullPatchModel) -> User:
    if not await is_username_unique(user_data.username, user.username):
        raise UsernameResponses.USERNAME_IN_USE.value
    user.update(**user_data.model_dump(exclude_defaults=True))
    return user


@router.delete("/{user_id}/", status_code=204)
async def delete_user(user: TargetUser) -> None:
    await user.delete()
