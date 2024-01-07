from fastapi import APIRouter

from app.models.users_db import User
from app.routes.reglog_rst import SignupResponses
from app.utils.users import UserResponses, is_username_unique

router = APIRouter(tags=["users mub"])


@router.post("/", response_model=User.FullModel, responses=SignupResponses.responses())
async def create_user(user_data: User.InputModel) -> User:
    if await User.find_first_by_kwargs(email=user_data.email) is not None:
        raise SignupResponses.EMAIL_IN_USE.value
    if await User.find_first_by_kwargs(username=user_data.username) is not None:
        raise SignupResponses.USERNAME_IN_USE.value
    return await User.create(**user_data.model_dump())


@router.get(
    "/{user_id}/",
    response_model=User.FullModel,
    responses=UserResponses.responses(keys=["USER_NOT_FOUND"]),
)
async def retrieve_user(user_id: int) -> User:
    user = await User.find_first_by_id(user_id)
    if user is None:
        raise UserResponses.USER_NOT_FOUND.value
    return user


@router.patch(
    "/{user_id}/",
    response_model=User.FullModel,
    responses=UserResponses.responses(),
    summary="Update user's data by id",
)
async def update_user(user_id: int, user_data: User.FullPatchModel) -> User:
    user = await User.find_first_by_id(user_id)
    if user is None:
        raise UserResponses.USER_NOT_FOUND.value
    if not await is_username_unique(user_data.username, user.username):
        raise UserResponses.USERNAME_IN_USE.value
    user.update(**user_data.model_dump(exclude_defaults=True))
    return user


@router.delete(
    "/{user_id}/",
    status_code=204,
    responses=UserResponses.responses(keys=["USER_NOT_FOUND"]),
)
async def delete_user(user_id: int) -> None:
    user = await User.find_first_by_id(user_id)
    if user is None:
        raise UserResponses.USER_NOT_FOUND.value
    await user.delete()
