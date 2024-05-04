from supbot.aiogram_extension import TelegramApp
from supbot.routers import support_team_tgm, support_tgm, vacancy_tgm

telegram_app = TelegramApp()

telegram_app.include_router(vacancy_tgm.router)
telegram_app.include_router(support_tgm.router)
telegram_app.include_router(support_team_tgm.router)
