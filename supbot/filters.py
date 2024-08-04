from typing import Any

from aiogram import F
from aiogram.filters import Command, Filter, or_f
from aiogram.fsm.context import FSMContext

from supbot.aiogram_extension import MessageExt
from supbot.models.support_db import SupportTicket
from supbot.texts import COMMAND_DESCRIPTIONS


class SupportTicketFilter(Filter):
    async def __call__(  # noqa: FNE005
        self,
        message: MessageExt,
        state: FSMContext,
    ) -> bool | dict[str, Any]:
        if message.chat.type == "private":
            message_thread_id = (await state.get_data()).get("thread_id")
        elif message.chat.type == "supergroup":
            message_thread_id = message.message_thread_id
        else:
            return False

        ticket = await SupportTicket.find_first_by_id(message_thread_id)

        if ticket is None or ticket.closed:
            return False

        return {"ticket": ticket}


def command_filter(command: str) -> Filter:
    return or_f(
        Command(command),
        F.text == COMMAND_DESCRIPTIONS[f"/{command}"],
    )
