from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove
from magic_filter import F

from app.routes.forms_rst import VacancyFormSchema, apply_for_vacancy
from supbot import texts
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
@router.message(F.text == texts.EXIT)
async def handle_exit(message: MessageExt, state: FSMContext) -> None:
    await message.answer(
        text=texts.HANDLE_EXIT_MESSAGE, reply_markup=ReplyKeyboardRemove()
    )
    await state.clear()


@router.message(Command("vacancy"), F.chat.type == "private")
@router.message(VacancyApplication.sending_name, F.text == texts.BACK)
async def choose_vacancy(message: MessageExt, state: FSMContext) -> None:
    await state.set_state(VacancyApplication.choosing_vacancy)
    await message.answer(
        text=texts.CHOOSE_VACANCY_MESSAGE,
        reply_markup=ReplyKeyboardMarkup(
            keyboard=texts.VACANCY_CHOOSE_KEYBOARD_MARKUP,
            resize_keyboard=True,
        ),
    )


@router.message(VacancyApplication.choosing_vacancy, F.text)
@router.message(VacancyApplication.sending_telegram, F.text == texts.BACK)
async def send_name(message: MessageExt, state: FSMContext) -> None:
    await state.update_data(vacancy=message.text)
    await message.answer(
        text=texts.SEND_NAME_MESSAGE,
        reply_markup=ReplyKeyboardMarkup(
            keyboard=texts.NAVIGATION_KEYBOARD_MARKUP,
            resize_keyboard=True,
        ),
    )
    await state.set_state(VacancyApplication.sending_name)


@router.message(VacancyApplication.sending_name, F.text)
@router.message(VacancyApplication.sending_resume, F.text == texts.BACK)
async def send_telegram(message: MessageExt, state: FSMContext) -> None:
    await state.update_data(name=message.text)
    await state.set_state(VacancyApplication.sending_telegram)
    await message.answer(
        text=texts.SEND_TELEGRAM_MESSSAGE,
        reply_markup=ReplyKeyboardMarkup(
            keyboard=texts.SEND_TELEGRAM_KEYBOARD_MARKUP,
            resize_keyboard=True,
        ),
    )


@router.message(VacancyApplication.sending_telegram, F.text)
@router.message(VacancyApplication.sending_message, F.text == texts.BACK)
async def send_resume(message: MessageExt, state: FSMContext) -> None:
    if (
        message.text == texts.SEND_TELEGRAM_KEYBOARD_TEXT
        and message.from_user is not None
    ):
        await state.update_data(
            telegram=f"https://www.t.me/{message.from_user.username}"
        )
    else:
        await state.update_data(telegram=message.text)

    await message.answer(
        text=texts.SEND_RESUME_MESSAGE,
        reply_markup=ReplyKeyboardMarkup(
            keyboard=texts.NAVIGATION_KEYBOARD_MARKUP,
            resize_keyboard=True,
        ),
    )
    await state.set_state(VacancyApplication.sending_resume)


@router.message(VacancyApplication.sending_resume)
@router.message(VacancyApplication.sending_message, F.text == texts.BACK)
async def send_info(message: MessageExt, state: FSMContext) -> None:
    await state.update_data(resume=message.text)
    await message.answer(
        text=texts.SEND_INFO_MESSAGE,
        reply_markup=ReplyKeyboardMarkup(
            keyboard=texts.NAVIGATION_KEYBOARD_MARKUP_WITH_SKIP,
            resize_keyboard=True,
        ),
    )
    await state.set_state(VacancyApplication.sending_message)


@router.message(VacancyApplication.sending_message, F.text)
async def final(message: MessageExt, state: FSMContext) -> None:
    if message.text != texts.SKIP:
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
        text=texts.VACANCY_FINAL_MESSAGE,
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.clear()
