from asyncio import AbstractEventLoop, get_running_loop
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import AsyncExitStack, asynccontextmanager

from aio_pika import connect_robust
from aio_pika.abc import AbstractRobustConnection
from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from starlette.requests import Request
from starlette.responses import Response
from starlette.staticfiles import StaticFiles

from app import pochta, supbot, users
from app.common.config import (
    DATABASE_MIGRATED,
    MQ_URL,
    PRODUCTION_MODE,
    Base,
    engine,
    pochta_producer,
    redis_pool,
    sessionmaker,
)
from app.common.sqlalchemy_ext import session_context
from app.common.starlette_cors_ext import CorrectCORSMiddleware


async def reinit_database() -> None:  # pragma: no cover
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


async def connect_rabbit() -> AbstractRobustConnection:
    loop: AbstractEventLoop = get_running_loop()
    connection = await connect_robust(MQ_URL, loop=loop)
    await pochta_producer.connect(connection)
    return connection


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    if not PRODUCTION_MODE and not DATABASE_MIGRATED:
        await reinit_database()

    rabbit_connection = await connect_rabbit()

    async with AsyncExitStack() as stack:
        await stack.enter_async_context(users.lifespan())
        await stack.enter_async_context(supbot.lifespan())
        await stack.enter_async_context(pochta.lifespan())
        yield

    await rabbit_connection.close()
    await redis_pool.disconnect()


app = FastAPI(
    title="xi.auth",
    docs_url=None,
    redoc_url=None,
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html() -> Response:
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="xi.auth",
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css",
        swagger_favicon_url=(
            '/static/favicon-for-light.svg">\n'
            + '<link rel="icon" href="/static/favicon-for-dark.svg" '
            + 'media="(prefers-color-scheme: dark)'
        ),
    )


app.add_middleware(
    CorrectCORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(pochta.api_router)
app.include_router(users.api_router)
app.include_router(supbot.api_router)


@app.middleware("http")
async def database_session_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    async with sessionmaker.begin() as session:
        session_context.set(session)
        return await call_next(request)
