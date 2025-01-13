from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends

from app.common.config import settings
from app.common.fastapi_ext import APIRouterExt
from app.users.routes import (
    avatar_rst,
    current_user_rst,
    email_confirmation_rst,
    forms_rst,
    onboarding_rst,
    password_reset_rst,
    proxy_rst,
    reglog_rst,
    sessions_mub,
    sessions_rst,
    users_mub,
    users_rst,
)
from app.users.utils.authorization import authorize_user
from app.users.utils.mub import MUBProtection

outside_router = APIRouterExt(prefix="/api")
outside_router.include_router(reglog_rst.router)
outside_router.include_router(forms_rst.router)
outside_router.include_router(
    email_confirmation_rst.router, prefix="/email-confirmation"
)
outside_router.include_router(password_reset_rst.router, prefix="/password-reset")

authorized_router = APIRouterExt(prefix="/api", dependencies=[Depends(authorize_user)])
authorized_router.include_router(onboarding_rst.router, prefix="/onboarding")
authorized_router.include_router(users_rst.router, prefix="/users")
authorized_router.include_router(current_user_rst.router, prefix="/users/current")
authorized_router.include_router(avatar_rst.router, prefix="/users/current/avatar")
authorized_router.include_router(sessions_rst.router, prefix="/sessions")

mub_router = APIRouterExt(prefix="/mub", dependencies=[MUBProtection])
mub_router.include_router(users_mub.router, prefix="/users")
mub_router.include_router(sessions_mub.router, prefix="/users/{user_id}/sessions")

api_router = APIRouterExt()
api_router.include_router(outside_router)
api_router.include_router(authorized_router)
api_router.include_router(mub_router)
api_router.include_router(proxy_rst.router)


@asynccontextmanager
async def lifespan() -> AsyncIterator[None]:
    settings.avatars_path.mkdir(exist_ok=True)
    yield
