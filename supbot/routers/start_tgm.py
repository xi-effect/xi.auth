from aiogram import Router
from aiogram.filters import CommandStart, StateFilter
from aiogram.types import ReplyKeyboardMarkup

from supbot.aiogram_extension import MessageExt
from supbot.texts import MAIN_MENU_KEYBOARD_MARKUP, WELCOME_MESSAGE

router = Router(name="start")


@router.message(StateFilter(None), CommandStart())
async def start_bot(message: MessageExt) -> None:
    await message.answer(
        WELCOME_MESSAGE,
        reply_markup=ReplyKeyboardMarkup(
            keyboard=MAIN_MENU_KEYBOARD_MARKUP, resize_keyboard=True
        ),
    )
