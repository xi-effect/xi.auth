from fastapi import APIRouter, Request

from supbot.main import telegram_app

router = APIRouter()


@router.post("/updates/", status_code=204)
async def feed_update_from_telegram(request: Request) -> None:
    await telegram_app.dispatcher.feed_webhook_update(
        telegram_app.bot, await request.json()
    )