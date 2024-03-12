import logging
from asyncio import create_task

from aiogram import Bot, Dispatcher
from aiogram.methods import GetUpdates
from httpx import AsyncClient

from app.common.config import (
    PRODUCTION_MODE,
    SUPBOT_CHANNEL_ID,
    SUPBOT_GROUP_ID,
    SUPBOT_POLLING,
    SUPBOT_TOKEN,
    SUPBOT_WEBHOOK_URL,
    TESTING_MODE,
)
from supbot.main import telegram_app


async def run_telegram_polling(polling_timeout: int = 30) -> None:
    api_client = AsyncClient(base_url=f"{SUPBOT_WEBHOOK_URL}/api/telegram")

    # Partially copied from a protected function:
    # https://github.com/aiogram/aiogram/blob/756cfeba0a257d80b9450adda5c6f4eda743c031/aiogram/dispatcher/dispatcher.py#L191-L247
    get_updates = GetUpdates(timeout=polling_timeout)
    while True:  # noqa: WPS457  # we know
        updates = await telegram_app.bot(get_updates)
        for update in updates:
            await api_client.post("/updates/", json=update.model_dump(mode="json"))
            get_updates.offset = update.update_id + 1


def maybe_initialize_telegram_app() -> None:
    if (
        not TESTING_MODE
        and SUPBOT_TOKEN is not None
        and SUPBOT_GROUP_ID is not None
        and SUPBOT_CHANNEL_ID is not None
    ):
        telegram_app.initialize(
            bot=Bot(SUPBOT_TOKEN),
            dispatcher=Dispatcher(
                group_id=int(SUPBOT_GROUP_ID),
                channel_id=int(SUPBOT_CHANNEL_ID),
            ),
        )
        if SUPBOT_POLLING:
            create_task(run_telegram_polling())
    elif PRODUCTION_MODE:
        logging.warning("Configuration for supbot is missing")
