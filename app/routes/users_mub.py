from fastapi import APIRouter, HTTPException
from starlette.status import HTTP_404_NOT_FOUND

from app.models.users_db import User, UserPasswordModel

router = APIRouter(tags=["users mub"])


@router.post("/", response_model=User.FullModel)
async def create_user(user_data: UserPasswordModel) -> User:
    return await User.create(**user_data.model_dump())


@router.get("/{user_id}", response_model=User.FullModel)
async def retrieve_user(user_id: int) -> User:
    user = await User.find_first_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=User.not_found_text)
    return user


@router.put("/{user_id}", response_model=User.FullModel)
async def update_user(user_id: int, user_data: User.PatchModel) -> User:
    user = await User.find_first_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=User.not_found_text)

    user.update(**user_data.model_dump(exclude_defaults=True))
    return user
