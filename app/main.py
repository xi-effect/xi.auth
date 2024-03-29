from asyncio import AbstractEventLoop, get_running_loop
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from aio_pika import connect_robust
from fastapi import APIRouter, FastAPI
from starlette.requests import Request
from starlette.responses import Response

from app.common.config import (
    AVATARS_PATH,
    DATABASE_MIGRATED,
    MQ_URL,
    PRODUCTION_MODE,
    Base,
    engine,
    pochta_producer,
    sessionmaker,
)
from app.common.sqla import session_context
from app.routes import (
    avatar_rst,
    current_user_rst,
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
from app.utils.cors import CorrectCORSMiddleware
from app.utils.mub import MUBProtection


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    if not PRODUCTION_MODE and not DATABASE_MIGRATED:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

    loop: AbstractEventLoop = get_running_loop()
    connection = await connect_robust(MQ_URL, loop=loop)
    await pochta_producer.connect(connection)
    AVATARS_PATH.mkdir(exist_ok=True)

    yield
    await connection.close()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CorrectCORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API
app.include_router(reglog_rst.router, prefix="/api")
app.include_router(onboarding_rst.router, prefix="/api/onboarding")
app.include_router(users_rst.router, prefix="/api/users")
app.include_router(current_user_rst.router, prefix="/api/users/current")
app.include_router(avatar_rst.router, prefix="/api/users/current/avatar")
app.include_router(sessions_rst.router, prefix="/api/sessions")
app.include_router(password_reset_rst.router, prefix="/api/password-reset")
app.include_router(forms_rst.router, prefix="/api")

# MUB
mub_router = APIRouter()
mub_router.include_router(users_mub.router, prefix="/mub/users")
mub_router.include_router(sessions_mub.router, prefix="/mub/users/{user_id}/sessions")

app.include_router(mub_router, dependencies=[MUBProtection])

# Proxy
app.include_router(proxy_rst.router, prefix="/proxy/auth")


@app.middleware("http")
async def database_session_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    async with sessionmaker.begin() as session:
        session_context.set(session)
        return await call_next(request)
