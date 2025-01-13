import logging
from asyncio import create_task

from aiogram import Bot, Dispatcher
from aiogram.methods import GetUpdates
from httpx import AsyncClient

from app.common.config import settings
from app.supbot.texts import BOT_COMMANDS
from app.supbot.utils.aiogram_ext import TelegramApp


async def run_telegram_polling(
    telegram_app: TelegramApp, webhook_url: str, polling_timeout: int = 30
) -> None:
    api_client = AsyncClient(base_url=f"{webhook_url}/api/telegram")

    # Partially copied from a protected function:
    # https://github.com/aiogram/aiogram/blob/756cfeba0a257d80b9450adda5c6f4eda743c031/aiogram/dispatcher/dispatcher.py#L191-L247
    get_updates = GetUpdates(timeout=polling_timeout)
    while True:  # noqa: WPS457  # we know
        updates = await telegram_app.bot(get_updates)
        for update in updates:
            await api_client.post(
                "/updates/", json=update.model_dump(mode="json", exclude_unset=True)
            )
            get_updates.offset = update.update_id + 1


async def maybe_initialize_telegram_app(telegram_app: TelegramApp) -> None:
    if not settings.is_testing_mode and settings.supbot is not None:
        telegram_app.initialize(
            bot=Bot(settings.supbot.token),
            dispatcher=Dispatcher(
                group_id=settings.supbot.group_id,
                channel_id=settings.supbot.channel_id,
            ),
        )
        await telegram_app.bot.set_my_commands(BOT_COMMANDS)
        if settings.supbot.polling:
            create_task(run_telegram_polling(telegram_app, settings.supbot.webhook_url))
    elif settings.production_mode:
        logging.warning("Configuration for supbot is missing")
