from fastapi import APIRouter, UploadFile

from app.common.responses import Responses
from app.models.users_db import Avatar
from app.services.avatar_service import AvatarResponses, AvatarService
from app.utils.authorization import AuthorizedUser

router = APIRouter(tags=["avatar_actions"])


@router.put("/update", status_code=201, responses=AvatarResponses.responses())
async def update_or_create_avatar(user: AuthorizedUser, file: UploadFile) -> None:
    await AvatarService.create_or_update(user.id, file)


class AvatarRD(Responses):
    NOT_FOUND = (404, "Avatar not found")


@router.get(
    "/get", response_model=AvatarService.response_model, responses=AvatarRD.responses()
)
async def get_avatar(user: AuthorizedUser) -> Avatar:
    return await AvatarService.get(user.id)


@router.delete("/delete", responses=AvatarRD.responses())
async def delete_avatar(user: AuthorizedUser) -> None:
    await AvatarService.delete(user.id)
