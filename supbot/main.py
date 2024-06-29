from supbot.aiogram_extension import TelegramApp
from supbot.routers import (
    error_handling_tgm,
    start_tgm,
    support_team_tgm,
    support_tgm,
    vacancy_tgm,
)

telegram_app = TelegramApp()

telegram_app.include_router(error_handling_tgm.router)
telegram_app.include_router(start_tgm.router)
telegram_app.include_router(vacancy_tgm.router)
telegram_app.include_router(support_tgm.router)
telegram_app.include_router(support_team_tgm.router)
