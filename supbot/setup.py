import logging

from aiogram import Bot, Dispatcher

from app.common.config import (
    PRODUCTION_MODE,
    SUPBOT_CHANNEL_ID,
    SUPBOT_GROUP_ID,
    SUPBOT_TOKEN,
    TESTING_MODE,
)
from supbot.main import telegram_app


def maybe_initialize_telegram_app() -> None:
    if (
        not TESTING_MODE
        and SUPBOT_TOKEN is not None
        and SUPBOT_GROUP_ID is not None
        and SUPBOT_CHANNEL_ID is not None
    ):  # pragma: no cover
        telegram_app.initialize(
            bot=Bot(SUPBOT_TOKEN),
            dispatcher=Dispatcher(
                group_id=int(SUPBOT_GROUP_ID),
                channel_id=int(SUPBOT_CHANNEL_ID),
            ),
        )
    elif PRODUCTION_MODE:
        logging.warning("Configuration for supbot is missing")
