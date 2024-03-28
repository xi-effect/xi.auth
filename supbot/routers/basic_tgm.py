from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from supbot import texts
from supbot.aiogram_extension import MessageExt

router = Router()


@router.message(CommandStart())
async def start_conversation(message: MessageExt) -> None:
    await message.answer(texts.START_MESSAGE)


@router.message()
async def echo_message(
    message: MessageExt,
    state: FSMContext,
    group_id: int,
    channel_id: int,
) -> None:
    # Temporary endpoint for testing local bot configuration & test capabilities

    current_state = await state.get_state()
    if current_state == "spam":
        await state.set_state("eggs")
    else:
        await state.set_state("spam")

    if message.chat.id == group_id or message.text is None:
        return
    await message.answer(str(current_state))
    await message.answer(message.text, entities=message.entities)
    await message.bot.send_message(
        chat_id=channel_id,
        text=message.text,
        entities=message.entities,
    )
