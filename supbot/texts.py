from aiogram.types import BotCommand, KeyboardButton, ReplyKeyboardMarkup

COMMANDS_DESCRIPTION = {
    "/support": "Обращение в поддержку",
    "/vacancy": "Наши вакансии",
}

BOT_COMMANDS: list[BotCommand] = [
    BotCommand(command="/support", description=COMMANDS_DESCRIPTION["/support"]),
    BotCommand(command="/vacancy", description=COMMANDS_DESCRIPTION["/vacancy"]),
]


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [[KeyboardButton(text=command.description) for command in BOT_COMMANDS]]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


WELCOME_TEXT = "Добро пожаловать!"

MAIN_MENU_MESSAGE = """
Выберите нужный пункт меню:
"""

MAIN_MENU_BUTTON_TEXT = "📋 Главное меню"

SUPPORT_TICKET_CLOSED_EMOJI_ID = "5237699328843200968"  # ✅
SUPPORT_TICKED_OPENED_EMOJI_ID = "5312241539987020022"  # 🔥
SUPPORT_ANSWER_DELIVERED_EMOJI = "⚡"
CLOSE_SUPPORT_BUTTON_TEXT = "❌ Закрыть обращение"
START_SUPPORT_MESSAGE = """
Пожалуйста, опишите вашу проблему
"""
WAIT_SUPPORT_MESSAGE = """
Ваше обращение направлено в поддержку
Все следующие сообщения мы также получим
Совсем скоро с вами свяжутся
Ожидайте...
"""
SUPPORT_TOPIC_NAME = "Обращение от "
CANCEL_SUPPORT_MESSAGE = """
Ваше обращение успешно закрыто
"""
CLOSE_SUPPORT_BY_USER_MESSAGE = """
Обращение закрыто пользователем
"""
TICKET_CLOSED_USER_BLOCKED_BOT = """
Пользователь заблокировал бота. Тикет закрыт автоматически.
"""
CLOSE_TICKET_BY_SUPPORT_MESSAGE = """
Ваше обращение закрыто сотрудником тех. поддержки
"""


TELEGRAM_BASE_URL = "https://www.t.me"

BACK_BUTTON_TEXT = "Назад"
SKIP_BUTTON_TEXT = "Пропустить"

# Vacancy Form Start
VACANCIES_WEBSITE_URL = "https://vacancy.xieffect.ru/vacancy"
EXIT_VACANCY_FORM_MESSAGE = "Будем ждать вас снова!"
STARTING_VACANCY_FORM_MESSAGE = f"""
Вы можете выбрать интересующую вакансию
через бота или по ссылке {VACANCIES_WEBSITE_URL}
"""
CHOOSE_VACANCY_MESSAGE = "Выберите вакансию или введите свою"
SEND_NAME_MESSAGE = "Как к вам можно обращаться?"
SEND_TELEGRAM_MESSAGE = "Ваш телеграм для обратной связи"
SEND_RESUME_MESSAGE = "Ссылка на ваше резюме"
WRONG_USER_MESSAGE = "Мы не поддерживаем такие сообщения"
SEND_INFO_MESSAGE = "Почти готово. Можете оставить для нас сообщение :)"
VACANCY_FORM_FINAL_MESSAGE = "Спасибо! Мы обязательно рассмотрим ваш отклик и ответим."
VACANCY_UNSUPPORTED_MESSAGE_TYPE = """
Пожалуйста, используйте только текстовые сообщения или кнопки для заполнения формы вакансии.
"""

CONTINUE_IN_BOT_KEYBOARD_TEXT = "Продолжить через бота"
VACANCY_FORM_EPILOGUE_KEYBOARD_MARKUP: list[list[KeyboardButton]] = [
    [
        KeyboardButton(text=CONTINUE_IN_BOT_KEYBOARD_TEXT),
        KeyboardButton(text=MAIN_MENU_BUTTON_TEXT),
    ],
]

NAVIGATION_KEYBOARD_MARKUP: list[list[KeyboardButton]] = [
    [KeyboardButton(text=BACK_BUTTON_TEXT), KeyboardButton(text=MAIN_MENU_BUTTON_TEXT)]
]

NAVIGATION_KEYBOARD_MARKUP_WITH_SKIP: list[list[KeyboardButton]] = [
    [KeyboardButton(text=SKIP_BUTTON_TEXT)],
    *NAVIGATION_KEYBOARD_MARKUP,
]

SPECIALIZATIONS: list[str] = [
    "Frontend разработчик",
    "Backend разработчик",
    "Графический дизайнер",
    "Product manager",
    "SMM-специалист",
]
CHOOSE_SPECIALIZATION_KEYBOARD_MARKUP: list[list[KeyboardButton]] = [
    *[[KeyboardButton(text=SPECIALIZATION)] for SPECIALIZATION in SPECIALIZATIONS],
    *NAVIGATION_KEYBOARD_MARKUP,
]

LEAVE_CURRENT_ACCOUNT_BUTTON_TEXT = "Оставить свой текущий аккаунт"
SEND_TELEGRAM_KEYBOARD_MARKUP: list[list[KeyboardButton]] = [
    [KeyboardButton(text=LEAVE_CURRENT_ACCOUNT_BUTTON_TEXT)],
    *NAVIGATION_KEYBOARD_MARKUP,
]
# Vacancy Form End
