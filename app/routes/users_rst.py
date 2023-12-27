from typing import Any

from fastapi import APIRouter

from app.models.users_db import User
from app.routes.reglog_rst import SignupResponses
from app.utils.authorization import AuthorizedResponses, AuthorizedUser

router = APIRouter(tags=["current user"], prefix="/current")


@router.get(
    "/home/",
    response_model=User.FullModel,
    responses=AuthorizedResponses.responses(),
)
async def get_user_data(user: AuthorizedUser) -> User:
    return user


@router.patch(
    "/profile/",
    response_model=User.FullModel,
    responses=AuthorizedResponses.responses(),
)
async def patch_user_data(
    patch_data: User.ProfilePatchModel, user: AuthorizedUser
) -> User:
    update_data: dict[str, Any] = patch_data.model_dump(exclude_defaults=True)
    if await user.username_verify(update_data.get("username")) is not None:
        raise SignupResponses.USERNAME_IN_USE.value
    user.update(**update_data)
    return user


@router.patch(
    "/customization/",
    response_model=User.CurrentThemeModel,
    responses=AuthorizedResponses.responses(),
)
async def patch_theme(theme_data: User.ThemeModel, user: AuthorizedUser) -> User:
    user.update(**theme_data.model_dump(exclude_defaults=True))
    return user
