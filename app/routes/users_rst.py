from fastapi import APIRouter

from app.models.users_db import User
from app.utils.authorization import AuthorizedResponses, AuthorizedUser

router = APIRouter(tags=["current user"])


@router.get(
    "/current/home/",
    response_model=User.FullModel,
    responses=AuthorizedResponses.responses(),
)
async def get_user_data(user: AuthorizedUser) -> User:
    return user
