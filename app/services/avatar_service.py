from pathlib import Path

import aiofiles
from fastapi import UploadFile

from app.common.config import AVATARS_PATH
from app.common.responses import Responses
from app.models.users_db import Avatar
from app.utils.authorization import AuthorizedResponses
from app.utils.magic import include_responses


@include_responses(AuthorizedResponses)
class AvatarResponses(Responses):
    TOO_LARGE = (422, "File too large")
    NOT_IMAGE = (422, "Image expected")
    SAME_IMAGE = (304, "Same image")
    NOT_FOUND = (404, "Avatar not found")


class AvatarService:
    response_model = Avatar.OutputModel

    @classmethod
    async def validate(cls, image: UploadFile) -> None:
        if image.size > 40000000:  # type: ignore[operator]
            raise AvatarResponses.TOO_LARGE.value
        if image.content_type.split("/")[0] != "image":  # type: ignore[union-attr]
            raise AvatarResponses.NOT_IMAGE.value

    @classmethod
    async def create_or_update(cls, user_id: int, image: UploadFile) -> None:
        url = AVATARS_PATH + image.filename  # type: ignore[operator]
        await cls.validate(image)
        if await Avatar.find_first_by_kwargs(URL=url):
            raise AvatarResponses.SAME_IMAGE.value

        current_avatar = await Avatar.find_first_by_id(user_id)
        if current_avatar:
            await current_avatar.delete()
            Path(current_avatar.URL).unlink()
        async with aiofiles.open(url, "w+b") as f:
            content = await image.read()
            await f.write(content)
        await Avatar.create(id=user_id, URL=url)

    @classmethod
    async def delete(cls, user_id: int) -> None:
        current_avatar = await Avatar.find_first_by_id(user_id)
        if current_avatar is None:
            raise AvatarResponses.NOT_FOUND.value
        Path(current_avatar.URL).unlink()
        await current_avatar.delete()

    @classmethod
    async def get(cls, user_id: int) -> Avatar:
        current_avatar = await Avatar.find_first_by_id(user_id)
        if current_avatar is None:
            raise AvatarResponses.NOT_FOUND.value

        return current_avatar
