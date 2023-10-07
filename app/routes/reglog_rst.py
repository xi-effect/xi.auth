from fastapi import APIRouter, HTTPException
from starlette.status import HTTP_409_CONFLICT

from app.common.exceptions import UnauthorizedException
from app.models.users_db import User, UserPasswordModel

router = APIRouter(tags=["reglog"])


@router.post("/signup", response_model=User.FullModel)
async def signup(user_data: UserPasswordModel) -> User:
    if await User.find_first_by_kwargs(email=user_data.email) is not None:
        raise HTTPException(
            status_code=HTTP_409_CONFLICT, detail="Email already in use"
        )

    # TODO send email
    # TODO create token & add as headers
    return await User.create(**user_data.model_dump())


@router.post("/signin", response_model=User.FullModel)
async def signin(user_data: User.InputModel) -> User:
    user = await User.find_first_by_kwargs(email=user_data.email)
    if user is None:
        raise UnauthorizedException(detail=User.not_found_text)

    if not user.is_password_valid(user_data.password):
        raise UnauthorizedException(detail="Wrong password")

    # TODO create token & add as headers
    return user
