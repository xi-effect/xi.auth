from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from magic_filter import F

from app.routes.forms_rst import VacancyFormSchema, apply_for_vacancy
from supbot.aiogram_extension import MessageExt

router = Router()


class VacancyApplication(StatesGroup):
    choosing_vacancy = State()
    sending_name = State()
    sending_telegram = State()
    sending_resume = State()
    sending_message = State()


@router.message(
    VacancyApplication.choosing_vacancy,
    VacancyApplication.sending_name,
    VacancyApplication.sending_telegram,
    VacancyApplication.sending_resume,
    VacancyApplication.sending_message,
)
@router.message(F.text == "Выйти из опроса")
async def handle_exit(message: MessageExt, state: FSMContext) -> None:
    await message.answer(
        text="Будем ждать вас снова!", reply_markup=ReplyKeyboardRemove()
    )
    await state.clear()


@router.message(Command("vacancy"), F.chat.type == "private")
@router.message(VacancyApplication.sending_name, F.text == "Назад")
async def choose_vacancy(message: MessageExt, state: FSMContext) -> None:
    await state.set_state(VacancyApplication.choosing_vacancy)
    await message.answer(
        text="Выберите вакансию или введите свою",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Frontend разработчик")],
                [KeyboardButton(text="Backend разработчик")],
                [KeyboardButton(text="Графический дизайнер")],
                [KeyboardButton(text="Product manager")],
                [KeyboardButton(text="SMM-специалист")],
                [KeyboardButton(text="Выйти из опроса")],
            ],
            resize_keyboard=True,
        ),
    )


@router.message(VacancyApplication.choosing_vacancy, F.text)
@router.message(VacancyApplication.sending_telegram, F.text == "Назад")
async def send_name(message: MessageExt, state: FSMContext) -> None:
    await state.update_data(vacancy=message.text)
    await message.answer(
        text="Как в вам можно обращаться?",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Назад"), KeyboardButton(text="Выйти из опроса")]
            ],
            resize_keyboard=True,
        ),
    )
    await state.set_state(VacancyApplication.sending_name)


@router.message(VacancyApplication.sending_name, F.text)
@router.message(VacancyApplication.sending_resume, F.text == "Назад")
async def send_telegram(message: MessageExt, state: FSMContext) -> None:
    await state.update_data(name=message.text)
    await state.set_state(VacancyApplication.sending_telegram)
    await message.answer(
        text="Ваш телеграм для обратной связи",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Оставить свой текущий аккаунт")],
                [KeyboardButton(text="Назад"), KeyboardButton(text="Выйти из опроса")],
            ],
            resize_keyboard=True,
        ),
    )


@router.message(VacancyApplication.sending_telegram, F.text)
@router.message(VacancyApplication.sending_message, F.text == "Назад")
async def send_resume(message: MessageExt, state: FSMContext) -> None:
    if (
        message.text == "Оставить свой текущий аккаунт"
        and message.from_user is not None
    ):
        await state.update_data(
            telegram=f"https://www.t.me/{message.from_user.username}"
        )
    else:
        await state.update_data(telegram=message.text)

    await message.answer(
        text="Ссылка на ваше резюме",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Назад"), KeyboardButton(text="Выйти из опроса")]
            ],
            resize_keyboard=True,
        ),
    )
    await state.set_state(VacancyApplication.sending_resume)


@router.message(VacancyApplication.sending_resume)
@router.message(VacancyApplication.sending_message, F.text == "Назад")
async def send_message(message: MessageExt, state: FSMContext) -> None:
    await state.update_data(resume=message.text)
    await message.answer(
        text="Почти готово. Можете оставить для нас сообщение :)",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Пропустить")],
                [KeyboardButton(text="Назад"), KeyboardButton(text="Выйти из опроса")],
            ],
            resize_keyboard=True,
        ),
    )
    await state.set_state(VacancyApplication.sending_message)


@router.message(VacancyApplication.sending_message, F.text)
async def final(message: MessageExt, state: FSMContext) -> None:
    if message.text != "Пропустить":
        await state.update_data(message=message.text)

    answers = await state.get_data()
    await apply_for_vacancy(
        VacancyFormSchema(
            name=answers["name"],
            position=answers["vacancy"],
            telegram=answers["telegram"],
            link=answers["resume"],
            message=answers.get("message", None),
        )
    )

    await message.answer(
        text="Спасибо! Мы обязательно рассмотрим ваш отклик и ответим.",
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.clear()
