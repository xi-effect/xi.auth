from aiogram import Router
from aiogram.filters import CommandStart, StateFilter

from supbot.aiogram_extension import MessageExt
from supbot.texts import WELCOME_TEXT, get_main_menu_keyboard

router = Router(name="main_menu")


@router.message(StateFilter(None), CommandStart())
async def start_command(message: MessageExt) -> None:
    await message.answer(WELCOME_TEXT, reply_markup=get_main_menu_keyboard())
