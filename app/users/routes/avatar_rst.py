from typing import Annotated

import filetype  # type: ignore[import-untyped]
from fastapi import File, UploadFile
from filetype.types.image import Webp  # type: ignore[import-untyped]

from app.common.fastapi_ext import APIRouterExt, Responses
from app.users.utils.authorization import AuthorizedUser

router = APIRouterExt(tags=["current user avatar"])


class AvatarResponses(Responses):
    WRONG_FORMAT = (415, "Invalid image format")


@router.put(
    "/",
    status_code=204,
    responses=AvatarResponses.responses(),
    summary="Upload a new user avatar",
)
async def update_or_create_avatar(
    user: AuthorizedUser,
    avatar: Annotated[UploadFile, File(description="image/webp")],
) -> None:
    if not filetype.match(avatar.file, [Webp()]):
        raise AvatarResponses.WRONG_FORMAT.value

    with user.avatar_path.open("wb") as file:
        file.write(await avatar.read())


@router.delete("/", status_code=204, summary="Remove current user avatar")
async def delete_avatar(user: AuthorizedUser) -> None:
    user.avatar_path.unlink(missing_ok=True)
