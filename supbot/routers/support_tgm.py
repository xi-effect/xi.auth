from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove

from supbot.aiogram_extension import MessageExt
from supbot.texts import (
    EXIT_SUPPORT_MESSAGE,
    MAIN_MENU_BUTTON_TEXT,
    START_SUPPORT_MESSAGE,
    WAIT_SUPPORT_MESSAGE,
)

router = Router(name="support")


class Support(StatesGroup):
    start = State()
    conversation = State()


@router.message(Command("support"), F.chat.type == "private")
async def start_support(message: MessageExt, state: FSMContext) -> None:
    await message.answer(
        text=START_SUPPORT_MESSAGE,
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=MAIN_MENU_BUTTON_TEXT)]],
            resize_keyboard=True,
        ),
    )
    await state.set_state(Support.start)


@router.message(Support.start, Support.conversation)
@router.message(F.text == MAIN_MENU_BUTTON_TEXT)
async def cancel_support(message: MessageExt, state: FSMContext) -> None:
    await message.answer(
        text=EXIT_SUPPORT_MESSAGE,
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.clear()


@router.message(Support.start)
async def create_support_ticket(
    message: MessageExt,
    state: FSMContext,
    channel_id: int,
) -> None:
    await message.bot.forward_message(
        chat_id=channel_id,
        from_chat_id=message.chat.id,
        message_id=message.message_id,
    )
    await message.answer(text=WAIT_SUPPORT_MESSAGE)
    await state.set_state(Support.conversation)
