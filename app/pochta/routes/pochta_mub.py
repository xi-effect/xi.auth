from app.common.config import REDIS_POCHTA_STREAM
from app.common.fastapi_ext import APIRouterExt
from app.pochta.dependencies.redis_dep import RedisConnection

router = APIRouterExt(tags=["pochta mub"])


@router.post("/")
async def home(r: RedisConnection) -> dict[str, str]:
    await r.xadd(
        REDIS_POCHTA_STREAM,
        {"key": "value"},
    )
    return {"msg": f"Message was added to stream {REDIS_POCHTA_STREAM}"}
