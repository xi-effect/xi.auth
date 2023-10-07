from fastapi import APIRouter
from starlette.status import HTTP_404_NOT_FOUND

from app.common.responses import Responses
from app.models.users_db import User, UserPasswordModel

router = APIRouter(tags=["users mub"])


@router.post("/", response_model=User.FullModel)
async def create_user(user_data: UserPasswordModel) -> User:
    return await User.create(**user_data.model_dump())


class UserResponses(Responses):
    USER_NOT_FOUND = (HTTP_404_NOT_FOUND, User.not_found_text)


@router.get(
    "/{user_id}",
    response_model=User.FullModel,
    responses=UserResponses.responses(),
)
async def retrieve_user(user_id: int) -> User:
    user = await User.find_first_by_id(user_id)
    if user is None:
        raise UserResponses.USER_NOT_FOUND.value
    return user


@router.put(
    "/{user_id}",
    response_model=User.FullModel,
    responses=UserResponses.responses(),
)
async def update_user(user_id: int, user_data: User.PatchModel) -> User:
    user = await User.find_first_by_id(user_id)
    if user is None:
        raise UserResponses.USER_NOT_FOUND.value

    user.update(**user_data.model_dump(exclude_defaults=True))
    return user
