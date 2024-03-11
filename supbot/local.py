from asyncio import run

from aiogram import Bot, Dispatcher

from app.common.config import SUPBOT_CHANNEL_ID, SUPBOT_GROUP_ID, SUPBOT_TOKEN
from supbot.main import telegram_app


def main() -> None:
    if SUPBOT_TOKEN is None:
        raise EnvironmentError("Environment variable 'SUPBOT_TOKEN' is not set")
    if SUPBOT_GROUP_ID is None:
        raise EnvironmentError("Environment variable 'SUPBOT_GROUP_ID' is not set")
    if SUPBOT_CHANNEL_ID is None:
        raise EnvironmentError("Environment variable 'SUPBOT_CHANNEL_ID' is not set")
    telegram_app.initialize(bot=Bot(SUPBOT_TOKEN), dispatcher=Dispatcher())
    run(telegram_app.dispatcher.start_polling(telegram_app.bot))
