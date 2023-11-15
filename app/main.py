from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import Response

from app.common.config import (
    DATABASE_RESET,
    DB_URL,
    PRODUCTION_MODE,
    Base,
    engine,
    sessionmaker,
)
from app.common.sqla import session_context
from app.routes import proxy_rst, reglog_rst, sessions_rst, users_mub, users_rst
from app.utils.cors import CorrectCORSMiddleware


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    if not PRODUCTION_MODE:
        async with engine.begin() as conn:
            if DB_URL.endswith("app.db") or DATABASE_RESET:
                await conn.run_sync(Base.metadata.drop_all)
            if not DB_URL.startswith("postgresql") or DATABASE_RESET:
                await conn.run_sync(Base.metadata.create_all)

    yield


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
app.include_router(users_rst.router, prefix="/api/users")
app.include_router(sessions_rst.router, prefix="/api/sessions")

# MUB
app.include_router(users_mub.router, prefix="/mub/users")

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
