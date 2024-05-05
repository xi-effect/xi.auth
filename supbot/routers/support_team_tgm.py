from aiogram import F, Router
from aiogram.fsm.storage.base import BaseStorage, StorageKey
from aiogram.types import ReplyKeyboardRemove
from aiogram.types.reaction_type_emoji import ReactionTypeEmoji

from supbot.aiogram_extension import MessageExt
from supbot.filters import SupportTicketFilter
from supbot.models.support_db import SupportTicket
from supbot.texts import (
    CLOSE_TICKET_BY_SUPPORT_MESSAGE,
    SUPPORT_ANSWER_DELIVERED_EMOJI,
    SUPPORT_TICKET_CLOSED_EMOJI_ID,
)

router = Router(name="support team")


@router.message(
    ~F.forum_topic_created,
    ~F.forum_topic_edited,
    ~F.forum_topic_closed,
    F.chat.type == "supergroup",
    SupportTicketFilter(),
)
async def send_message_to_user(
    message: MessageExt, group_id: int, ticket: SupportTicket
) -> None:
    await message.copy_to(chat_id=ticket.chat_id)
    await message.bot.set_message_reaction(
        chat_id=group_id,
        message_id=message.message_id,
        reaction=[ReactionTypeEmoji(emoji=SUPPORT_ANSWER_DELIVERED_EMOJI)],
    )


@router.message(
    F.forum_topic_closed,
    F.from_user.id != F.bot.id,
    F.chat.type == "supergroup",
    SupportTicketFilter(),
)
async def close_ticket_by_support(
    message: MessageExt, group_id: int, fsm_storage: BaseStorage, ticket: SupportTicket
) -> None:
    await message.bot.send_message(
        chat_id=ticket.chat_id,
        text=CLOSE_TICKET_BY_SUPPORT_MESSAGE,
        reply_markup=ReplyKeyboardRemove(),
    )
    await message.bot.edit_forum_topic(
        chat_id=group_id,
        message_thread_id=ticket.message_thread_id,
        icon_custom_emoji_id=SUPPORT_TICKET_CLOSED_EMOJI_ID,
    )

    key = StorageKey(message.bot.id, ticket.chat_id, ticket.chat_id)
    await fsm_storage.set_state(key, None)

    ticket.closed = True
