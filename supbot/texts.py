from aiogram.types import BotCommand, KeyboardButton

BOT_COMMANDS: list[BotCommand] = [
    BotCommand(command="/echo", description="Тестовая команда"),
    BotCommand(command="/support", description="Обращение в поддержку"),
    BotCommand(command="/vacancy", description="Попасть в команду"),
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

TELEGRAM_URL = "https://www.t.me"

BACK = "Назад"
EXIT = "Выйти"
SKIP = "Пропустить"

NAVIGATION_KEYBOARD_MARKUP: list[list[KeyboardButton]] = [
    [KeyboardButton(text=BACK), KeyboardButton(text=EXIT)]
]

NAVIGATION_KEYBOARD_MARKUP_WITH_SKIP: list[list[KeyboardButton]] = [
    [KeyboardButton(text=SKIP)],
    *NAVIGATION_KEYBOARD_MARKUP,
]

# Vacancy form
EXIT_VACANCY_FORM_MESSAGE = "Будем ждать вас снова!"
CHOOSE_VACANCY_MESSAGE = "Выберите вакансию или введите свою"
SEND_NAME_MESSAGE = "Как к вам можно обращаться?"
SEND_TELEGRAM_MESSAGE = "Ваш телеграм для обратной связи"
SEND_RESUME_MESSAGE = "Ссылка на ваше резюме"
SEND_INFO_MESSAGE = "Почти готово. Можете оставить для нас сообщение :)"
VACANCY_FINAL_MESSAGE = "Спасибо! Мы обязательно рассмотрим ваш отклик и ответим."

VACANCIES = [
    "Frontend разработчик",
    "Backend разработчик",
    "Графический дизайнер",
    "Product manager",
    "SMM-специалист",
]
VACANCY_CHOOSE_KEYBOARD_MARKUP: list[list[KeyboardButton]] = [
    *[[KeyboardButton(text=VACANCY)] for VACANCY in VACANCIES],
    [KeyboardButton(text=EXIT)],
]


PROVIDE_CURRENT_ACCOUNT = "Оставить свой текущий аккаунт"
SEND_TELEGRAM_KEYBOARD_MARKUP: list[list[KeyboardButton]] = [
    [KeyboardButton(text=PROVIDE_CURRENT_ACCOUNT)],
    *NAVIGATION_KEYBOARD_MARKUP,
]
