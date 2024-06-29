from aiogram import F, Router
from aiogram.filters import KICKED, ChatMemberUpdatedFilter
from aiogram.fsm.storage.base import BaseStorage, StorageKey
from aiogram.types import ChatMemberUpdated
from aiogram.types.reaction_type_emoji import ReactionTypeEmoji

from supbot.aiogram_extension import MessageExt
from supbot.filters import SupportTicketFilter
from supbot.models.support_db import SupportTicket
from supbot.texts import (
    CLOSE_TICKET_BY_SUPPORT_MESSAGE,
    SUPPORT_ANSWER_DELIVERED_EMOJI,
    SUPPORT_TICKET_CLOSED_EMOJI_ID,
    TICKET_CLOSED_USER_BLOCKED_BOT,
    get_main_menu_keyboard,
)

router = Router(name="support team")


@router.my_chat_member(
    ChatMemberUpdatedFilter(member_status_changed=KICKED),
    SupportTicketFilter(),
)
async def close_ticket_after_bot_blocked(
    event: ChatMemberUpdated,
    group_id: int,
    fsm_storage: BaseStorage,
    ticket: SupportTicket,
) -> None:
    await event.bot.edit_forum_topic(  # type: ignore
        chat_id=group_id,
        message_thread_id=ticket.message_thread_id,
        icon_custom_emoji_id=SUPPORT_TICKET_CLOSED_EMOJI_ID,
    )

    await event.bot.send_message(  # type: ignore
        chat_id=group_id,
        text=TICKET_CLOSED_USER_BLOCKED_BOT,
        message_thread_id=ticket.message_thread_id,
    )

    key = StorageKey(event.bot.id, ticket.chat_id, ticket.chat_id)  # type: ignore
    await fsm_storage.set_state(key, None)

    ticket.closed = True


@router.message(
    ~F.forum_topic_created,
    ~F.forum_topic_edited,
    ~F.forum_topic_closed,
    F.chat.type == "supergroup",
    SupportTicketFilter(),
)
async def send_message_to_user(
    message: MessageExt,
    group_id: int,
    ticket: SupportTicket,
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
    message: MessageExt,
    group_id: int,
    fsm_storage: BaseStorage,
    ticket: SupportTicket,
) -> None:
    await message.bot.send_message(
        chat_id=ticket.chat_id,
        text=CLOSE_TICKET_BY_SUPPORT_MESSAGE,
        reply_markup=get_main_menu_keyboard(),
    )
    await message.bot.edit_forum_topic(
        chat_id=group_id,
        message_thread_id=ticket.message_thread_id,
        icon_custom_emoji_id=SUPPORT_TICKET_CLOSED_EMOJI_ID,
    )

    key = StorageKey(message.bot.id, ticket.chat_id, ticket.chat_id)
    await fsm_storage.set_state(key, None)

    ticket.closed = True
