from typing import Annotated

from fastapi import APIRouter, HTTPException
from pydantic import AfterValidator
from starlette.status import HTTP_404_NOT_FOUND

from app.models.users_db import User

router = APIRouter(tags=["users mub"])


class UserPasswordModel(User.InputModel):
    password: Annotated[str, AfterValidator(User.generate_hash)]


@router.post("/", response_model=User.FullModel)
async def create_user(user_data: UserPasswordModel) -> User:
    return await User.create(**user_data.model_dump())


@router.get("/{user_id}", response_model=User.FullModel)
async def retrieve_user(user_id: int) -> User:
    user = await User.find_first_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="User not found")
    return user
