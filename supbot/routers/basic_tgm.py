from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from supbot import texts

router = Router()


@router.message(Command("start"))
async def start_conversation(message: Message) -> None:
    await message.answer(texts.START_MESSAGE)
