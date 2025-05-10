from typing import BinaryIO

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup

from app.common.bridges.config_bdg import public_users_bridge
from app.common.schemas.vacancy_form_sch import VacancyFormSchema
from app.supbot import texts
from app.supbot.utils.aiogram_ext import MessageExt, MessageFromUser
from app.supbot.utils.filters import DocumentErrorType, DocumentFilter, command_filter

router = Router()


class VacancyStates(StatesGroup):
    starting_form = State()
    sending_specialization = State()
    sending_name = State()
    sending_telegram = State()
    sending_resume = State()
    sending_comment = State()


@router.message(
    StateFilter(*VacancyStates.__all_states__), F.text == texts.MAIN_MENU_BUTTON_TEXT
)
async def exit_vacancy_form(message: MessageExt, state: FSMContext) -> None:
    await message.answer(
        text=texts.MAIN_MENU_MESSAGE,
        reply_markup=ReplyKeyboardMarkup(
            keyboard=texts.MAIN_MENU_KEYBOARD_MARKUP, resize_keyboard=True
        ),
    )
    await state.clear()


@router.message(command_filter("vacancy"), F.chat.type == "private", StateFilter(None))
@router.message(VacancyStates.sending_specialization, F.text == texts.BACK_BUTTON_TEXT)
async def start_vacancy_form(message: MessageExt, state: FSMContext) -> None:
    await state.set_state(VacancyStates.starting_form)
    await message.answer(
        text=texts.STARTING_VACANCY_FORM_MESSAGE,
        reply_markup=ReplyKeyboardMarkup(
            keyboard=texts.VACANCY_FORM_EPILOGUE_KEYBOARD_MARKUP,
            resize_keyboard=True,
        ),
    )


@router.message(
    VacancyStates.starting_form,
    F.text == texts.CONTINUE_IN_BOT_KEYBOARD_TEXT,
)
@router.message(VacancyStates.sending_name, F.text == texts.BACK_BUTTON_TEXT)
async def request_vacancy(message: MessageExt, state: FSMContext) -> None:
    await state.set_state(VacancyStates.sending_specialization)
    await message.answer(
        text=texts.CHOOSE_VACANCY_MESSAGE,
        reply_markup=ReplyKeyboardMarkup(
            keyboard=texts.CHOOSE_SPECIALIZATION_KEYBOARD_MARKUP,
            resize_keyboard=True,
        ),
    )


@router.message(VacancyStates.sending_specialization, F.text)
@router.message(VacancyStates.sending_telegram, F.text == texts.BACK_BUTTON_TEXT)
async def set_vacancy_and_request_name(message: MessageExt, state: FSMContext) -> None:
    if message.text != texts.BACK_BUTTON_TEXT:
        await state.update_data(position=message.text)
    await state.set_state(VacancyStates.sending_name)
    await message.answer(
        text=texts.SEND_NAME_MESSAGE,
        reply_markup=ReplyKeyboardMarkup(
            keyboard=texts.NAVIGATION_KEYBOARD_MARKUP,
            resize_keyboard=True,
        ),
    )


@router.message(VacancyStates.sending_name, F.text)
@router.message(VacancyStates.sending_resume, F.text == texts.BACK_BUTTON_TEXT)
async def set_name_and_request_telegram(message: MessageExt, state: FSMContext) -> None:
    if message.text != texts.BACK_BUTTON_TEXT:
        await state.update_data(name=message.text)
    await state.set_state(VacancyStates.sending_telegram)
    await message.answer(
        text=texts.SEND_TELEGRAM_MESSAGE,
        reply_markup=ReplyKeyboardMarkup(
            keyboard=texts.SEND_TELEGRAM_KEYBOARD_MARKUP,
            resize_keyboard=True,
        ),
    )


@router.message(VacancyStates.sending_telegram, F.text)
@router.message(
    VacancyStates.sending_comment, F.text == texts.BACK_BUTTON_TEXT, F.from_user
)
async def set_telegram_and_request_resume(
    message: MessageFromUser, state: FSMContext
) -> None:
    if message.text == texts.LEAVE_CURRENT_ACCOUNT_BUTTON_TEXT:
        await state.update_data(
            telegram=f"{texts.TELEGRAM_BASE_URL}/{message.from_user.username}"
        )
    elif message.text != texts.BACK_BUTTON_TEXT:
        await state.update_data(telegram=message.text)
    await state.set_state(VacancyStates.sending_resume)

    await message.answer(
        text=texts.SEND_RESUME_MESSAGE,
        reply_markup=ReplyKeyboardMarkup(
            keyboard=texts.NAVIGATION_KEYBOARD_MARKUP,
            resize_keyboard=True,
        ),
    )


@router.message(VacancyStates.sending_resume, DocumentFilter())
async def set_resume_and_request_comment(
    message: MessageExt, document_data: tuple[str, BinaryIO, str], state: FSMContext
) -> None:
    await state.update_data(resume=document_data)
    await state.set_state(VacancyStates.sending_comment)
    await message.answer(
        text=texts.SEND_INFO_MESSAGE,
        reply_markup=ReplyKeyboardMarkup(
            keyboard=texts.NAVIGATION_KEYBOARD_MARKUP_WITH_SKIP,
            resize_keyboard=True,
        ),
    )


@router.message(VacancyStates.sending_comment, F.text)
async def submit_vacancy_form(message: MessageExt, state: FSMContext) -> None:
    answers = await state.get_data()
    if message.text != texts.SKIP_BUTTON_TEXT:
        answers["message"] = message.text

    await public_users_bridge.apply_for_vacancy(
        vacancy_form=VacancyFormSchema(
            position=answers["position"],
            name=answers["name"],
            telegram=answers["telegram"],
            message=answers.get("message"),
        ),
        resume=answers["resume"],
    )

    await message.answer(
        text=texts.VACANCY_FORM_FINAL_MESSAGE,
        reply_markup=ReplyKeyboardMarkup(
            keyboard=texts.MAIN_MENU_KEYBOARD_MARKUP, resize_keyboard=True
        ),
    )
    await state.clear()


@router.message(
    VacancyStates.sending_resume, DocumentFilter(DocumentErrorType.NO_DOCUMENT)
)
async def handle_missing_document(message: MessageExt) -> None:
    await message.answer(texts.VACANCY_NO_DOCUMENT_MESSAGE)


@router.message(
    VacancyStates.sending_resume, DocumentFilter(DocumentErrorType.WRONG_MIME_TYPE)
)
async def handle_unsupported_document_type(message: MessageExt) -> None:
    await message.answer(texts.VACANCY_UNSUPPORTED_DOCUMENT_TYPE_MESSAGE)


@router.message(
    VacancyStates.sending_resume, DocumentFilter(DocumentErrorType.FILE_TO_LARGE)
)
async def handle_unsupported_document_size(message: MessageExt) -> None:
    await message.answer(texts.VACANCY_DOCUMENT_TOO_LARGE_MESSAGE)


@router.message(
    StateFilter(*VacancyStates.__all_states__),
    ~F.text,
)
async def handle_unsupported_message(message: MessageExt) -> None:
    await message.answer(text=texts.VACANCY_INVALID_INPUT_TYPE_MESSAGE)
