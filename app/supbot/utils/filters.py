from enum import StrEnum
from typing import Any

from aiogram import F
from aiogram.filters import Command, Filter, or_f
from aiogram.fsm.context import FSMContext
from filetype import filetype  # type: ignore[import-untyped]
from filetype.types.archive import Pdf  # type: ignore[import-untyped]

from app.supbot import texts
from app.supbot.models.support_db import SupportTicket
from app.supbot.utils.aiogram_ext import MessageExt


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
        else:  # pragma: no cover  # exclusive situations, maybe they could be covered
            return False

        ticket = await SupportTicket.find_first_by_id(message_thread_id)

        if ticket is None or ticket.closed:  # pragma: no cover
            return False

        return {"ticket": ticket}


class DocumentErrorType(StrEnum):
    NO_DOCUMENT = "no_document"
    WRONG_MIME_TYPE = "wrong_mime_type"
    FILE_TO_LARGE = "file_to_large"


class DocumentFilter(Filter):
    MAX_DOCUMENT_SIZE: int = 10 * 2**20

    def __init__(
        self,
        expected_error: str | None = None,
        max_size: int = MAX_DOCUMENT_SIZE,
        mime_type: str = "application/pdf",
    ) -> None:
        self.expected_error = expected_error
        self.max_size = max_size
        self.mime_type = mime_type

    async def __call__(  # noqa: FNE005
        self,
        message: MessageExt,
    ) -> bool | dict[str, Any]:
        if message.document is None:
            return self.expected_error == DocumentErrorType.NO_DOCUMENT

        if message.document.mime_type != self.mime_type:
            return self.expected_error == DocumentErrorType.WRONG_MIME_TYPE
        if (
            message.document.file_size is None
            or message.document.file_size >= self.max_size
        ):
            return self.expected_error == DocumentErrorType.FILE_TO_LARGE

        content = await message.bot.download(message.document.file_id)

        match self.mime_type:
            case "application/pdf":
                if not filetype.match(content, [Pdf()]):
                    return self.expected_error == DocumentErrorType.WRONG_MIME_TYPE
        return {
            "document_data": (
                message.document.file_name,
                content,
                message.document.mime_type,
            )
        }


def command_filter(command: str) -> Filter:
    return or_f(
        Command(command),
        F.text == texts.COMMAND_DESCRIPTIONS[f"/{command}"],
    )
