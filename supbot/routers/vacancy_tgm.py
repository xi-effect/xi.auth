from aiogram import F, Router
from aiogram.filters import Command, Filter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove

from app.routes.forms_rst import VacancyFormSchema, apply_for_vacancy
from supbot import texts
from supbot.aiogram_extension import MessageExt

router = Router()


class VacancyApplication(StatesGroup):
    responding_to_the_epilogue = State()
    choosing_vacancy = State()
    sending_name = State()
    sending_telegram = State()
    sending_resume = State()
    sending_info = State()


class VacancyExitFilter(Filter):
    async def __call__(  # noqa: FNE005
        self, message: MessageExt, state: FSMContext
    ) -> bool:
        return await state.get_state() in {
            VacancyApplication.responding_to_the_epilogue,
            VacancyApplication.choosing_vacancy,
            VacancyApplication.sending_name,
            VacancyApplication.sending_telegram,
            VacancyApplication.sending_resume,
            VacancyApplication.sending_info,
        } and (message.text == texts.EXIT)


@router.message(VacancyExitFilter())
async def exit_vacancy_form(message: MessageExt, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        text=texts.EXIT_VACANCY_FORM_MESSAGE, reply_markup=ReplyKeyboardRemove()
    )


@router.message(Command("vacancy"), F.chat.type == "private")
@router.message(VacancyApplication.choosing_vacancy, F.text == texts.BACK)
async def start_vacancy_form_epilogue(message: MessageExt, state: FSMContext) -> None:
    await state.set_state(VacancyApplication.responding_to_the_epilogue)
    await message.answer(
        text=texts.STARTING_VACANCY_FORM_MESSAGE,
        reply_markup=ReplyKeyboardMarkup(
            keyboard=texts.VACANCY_EPILOGUE_KEYBOARD_MARKUP,
            resize_keyboard=True,
        ),
    )


@router.message(
    VacancyApplication.responding_to_the_epilogue,
    F.text == texts.CONTINUE_IN_BOT_KEYBOARD_TEXT,
)
@router.message(VacancyApplication.sending_name, F.text == texts.BACK)
async def request_vacancy(message: MessageExt, state: FSMContext) -> None:
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
async def set_vacancy_and_request_name(message: MessageExt, state: FSMContext) -> None:
    if message.text != texts.BACK:
        await state.update_data(vacancy=message.text)
    await state.set_state(VacancyApplication.sending_name)
    await message.answer(
        text=texts.SEND_NAME_MESSAGE,
        reply_markup=ReplyKeyboardMarkup(
            keyboard=texts.NAVIGATION_KEYBOARD_MARKUP,
            resize_keyboard=True,
        ),
    )


@router.message(VacancyApplication.sending_name, F.text)
@router.message(VacancyApplication.sending_resume, F.text == texts.BACK)
async def set_name_and_request_telegram(message: MessageExt, state: FSMContext) -> None:
    if message.text != texts.BACK:
        await state.update_data(name=message.text)
    await state.set_state(VacancyApplication.sending_telegram)
    await message.answer(
        text=texts.SEND_TELEGRAM_MESSAGE,
        reply_markup=ReplyKeyboardMarkup(
            keyboard=texts.SEND_TELEGRAM_KEYBOARD_MARKUP,
            resize_keyboard=True,
        ),
    )


@router.message(VacancyApplication.sending_telegram, F.text)
@router.message(VacancyApplication.sending_info, F.text == texts.BACK)
async def set_telegram_and_request_resume(
    message: MessageExt, state: FSMContext
) -> None:
    if message.text == texts.PROVIDE_CURRENT_ACCOUNT and message.from_user is not None:
        await state.update_data(
            telegram=f"{texts.TELEGRAM_URL}/{message.from_user.username}"
        )
    elif message.text != texts.BACK:
        await state.update_data(telegram=message.text)
    await state.set_state(VacancyApplication.sending_resume)

    await message.answer(
        text=texts.SEND_RESUME_MESSAGE,
        reply_markup=ReplyKeyboardMarkup(
            keyboard=texts.NAVIGATION_KEYBOARD_MARKUP,
            resize_keyboard=True,
        ),
    )


@router.message(VacancyApplication.sending_resume)
@router.message(VacancyApplication.sending_info, F.text == texts.BACK)
async def set_resume_and_request_info(message: MessageExt, state: FSMContext) -> None:
    if message.text != texts.BACK:
        await state.update_data(resume=message.text)
    await state.set_state(VacancyApplication.sending_info)
    await message.answer(
        text=texts.SEND_INFO_MESSAGE,
        reply_markup=ReplyKeyboardMarkup(
            keyboard=texts.NAVIGATION_KEYBOARD_MARKUP_WITH_SKIP,
            resize_keyboard=True,
        ),
    )


@router.message(VacancyApplication.sending_info, F.text)
async def finish_vacancy_form(message: MessageExt, state: FSMContext) -> None:
    if message.text != texts.SKIP:
        await state.update_data(message=message.text)

    answers = await state.get_data()
    await state.clear()
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
