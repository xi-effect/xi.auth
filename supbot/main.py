from supbot.aiogram_extension import TelegramApp
from supbot.routers import basic_tgm

telegram_app = TelegramApp()

telegram_app.include_router(basic_tgm.router)
