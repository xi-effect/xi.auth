from supbot.aiogram_extension import TelegramApp
from supbot.routers import basic_tgm, vacancy_tgm, support_tgm

telegram_app = TelegramApp()

telegram_app.include_router(vacancy_tgm.router)
telegram_app.include_router(support_tgm.router)
telegram_app.include_router(basic_tgm.router)
