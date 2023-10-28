from fastapi import APIRouter

from app.models.users_db import User
from app.utils.authorization import AuthorizedResponses, AuthorizedUser

router = APIRouter(tags=["sessions mub"])


@router.get(
    "/current/user/",
    response_model=User.FullModel,
    responses=AuthorizedResponses.responses(),
)
async def user_from_session(user: AuthorizedUser) -> User:
    return user
