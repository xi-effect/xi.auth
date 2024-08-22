from fastapi import Request

from app.common.fastapi_ext import APIRouterExt
from supbot.main import telegram_app

router = APIRouterExt()


@router.post("/updates/", status_code=204, summary="Execute telegram webhook")
async def feed_update_from_telegram(request: Request) -> None:
    await telegram_app.dispatcher.feed_webhook_update(
        telegram_app.bot, await request.json()
    )
