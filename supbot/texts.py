from aiogram.types import BotCommand

BOT_COMMANDS: list[BotCommand] = [
    BotCommand(command="/echo", description="Тестовая команда"),
    BotCommand(command="/support", description="Обращение в поддержку"),
]

START_MESSAGE = """
Привет!
Я xi.supbot!
"""

MAIN_MENU_BUTTON_TEXT = "📋 Главное меню"

START_SUPPORT_MESSAGE = """
Пожалуйста, опишите вашу проблему
"""

WAIT_SUPPORT_MESSAGE = """
Ваше обращение направлено в поддержку
Совсем скоро с вами свяжутся
Ожидайте...
"""

EXIT_SUPPORT_MESSAGE = """
Обращение успешно закрыто
"""
