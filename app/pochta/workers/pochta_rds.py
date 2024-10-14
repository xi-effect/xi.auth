from pydantic import BaseModel

from app.common.config import REDIS_POCHTA_STREAM
from app.common.redis_ext import RedisRouter


class PochtaSchema(BaseModel):
    key: str


router = RedisRouter()


@router.add_consumer(
    stream_name=REDIS_POCHTA_STREAM,
    group_name="pochta:group",
    consumer_name="pochta_consumer",
)
async def process_email_message(message: PochtaSchema) -> None:
    print(f"Message: {message}")  # noqa T201 Temporary print for debugging
