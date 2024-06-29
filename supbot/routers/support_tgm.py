from aiogram import F, Router
from aiogram.filters import KICKED, ChatMemberUpdatedFilter, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.base import BaseStorage, StorageKey
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from supbot.aiogram_extension import ChatMemberUpdatedExt, MessageExt
from supbot.filters import SupportTicketFilter, command_filter
from supbot.models.support_db import SupportTicket
from supbot.texts import (
    CANCEL_SUPPORT_MESSAGE,
    CLOSE_SUPPORT_BUTTON_TEXT,
    CLOSE_SUPPORT_BY_USER_MESSAGE,
    CLOSE_TICKET_AFTER_USER_BANNED_BOT_MESSAGE,
    MAIN_MENU_BUTTON_TEXT,
    MAIN_MENU_KEYBOARD_MARKUP,
    MAIN_MENU_MESSAGE,
    START_SUPPORT_MESSAGE,
    SUPPORT_TICKED_OPENED_EMOJI_ID,
    SUPPORT_TICKET_CLOSED_EMOJI_ID,
    SUPPORT_TOPIC_NAME,
    WAIT_SUPPORT_MESSAGE,
)

router = Router(name="support")


class Support(StatesGroup):
    start = State()
    conversation = State()


@router.message(
    StateFilter(None),
    command_filter("support"),
    F.chat.type == "private",
)
async def start_support(message: MessageExt, state: FSMContext) -> None:
    await message.answer(
        text=START_SUPPORT_MESSAGE,
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=MAIN_MENU_BUTTON_TEXT)]],
            resize_keyboard=True,
        ),
    )
    await state.set_state(Support.start)


@router.message(Support.start, F.text == MAIN_MENU_BUTTON_TEXT)
async def exit_support(message: MessageExt, state: FSMContext) -> None:
    await message.answer(
        text=MAIN_MENU_MESSAGE,
        reply_markup=ReplyKeyboardMarkup(
            keyboard=MAIN_MENU_KEYBOARD_MARKUP, resize_keyboard=True
        ),
    )
    await state.clear()


@router.message(Support.start)
async def create_support_ticket(
    message: MessageExt, state: FSMContext, group_id: int
) -> None:
    topic = await message.bot.create_forum_topic(
        chat_id=group_id,
        name=f"{SUPPORT_TOPIC_NAME}{message.chat.username}",
        icon_custom_emoji_id=SUPPORT_TICKED_OPENED_EMOJI_ID,
    )
    await SupportTicket.create(
        message_thread_id=topic.message_thread_id,
        chat_id=message.chat.id,
    )
    await message.copy_to(
        chat_id=group_id,
        message_thread_id=topic.message_thread_id,
    )
    await message.answer(
        text=WAIT_SUPPORT_MESSAGE,
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=CLOSE_SUPPORT_BUTTON_TEXT)]],
            resize_keyboard=True,
        ),
    )
    await state.update_data(thread_id=topic.message_thread_id)
    await state.set_state(Support.conversation)


@router.message(
    Support.conversation,
    F.text != CLOSE_SUPPORT_BUTTON_TEXT,
    SupportTicketFilter(),
)
async def send_message_to_support(
    message: MessageExt, group_id: int, ticket: SupportTicket
) -> None:
    await message.copy_to(
        chat_id=group_id,
        message_thread_id=ticket.message_thread_id,
    )


@router.message(
    Support.conversation,
    F.text == CLOSE_SUPPORT_BUTTON_TEXT,
    SupportTicketFilter(),
)
async def close_support_ticket_by_user(
    message: MessageExt,
    state: FSMContext,
    group_id: int,
    ticket: SupportTicket,
) -> None:
    await message.bot.close_forum_topic(
        chat_id=group_id,
        message_thread_id=ticket.message_thread_id,
    )
    await message.bot.edit_forum_topic(
        chat_id=group_id,
        message_thread_id=ticket.message_thread_id,
        icon_custom_emoji_id=SUPPORT_TICKET_CLOSED_EMOJI_ID,
    )
    await message.bot.send_message(
        chat_id=group_id,
        text=CLOSE_SUPPORT_BY_USER_MESSAGE,
        message_thread_id=ticket.message_thread_id,
    )
    await message.answer(
        text=CANCEL_SUPPORT_MESSAGE,
        reply_markup=ReplyKeyboardMarkup(
            keyboard=MAIN_MENU_KEYBOARD_MARKUP, resize_keyboard=True
        ),
    )

    ticket.closed = True

    await state.clear()


@router.my_chat_member(
    ChatMemberUpdatedFilter(member_status_changed=KICKED),
    SupportTicketFilter(),
)
async def close_ticket_after_bot_blocked(
    event: ChatMemberUpdatedExt,
    group_id: int,
    fsm_storage: BaseStorage,
    ticket: SupportTicket,
) -> None:
    await event.bot.close_forum_topic(
        chat_id=group_id,
        message_thread_id=ticket.message_thread_id,
    )
    await event.bot.edit_forum_topic(
        chat_id=group_id,
        message_thread_id=ticket.message_thread_id,
        icon_custom_emoji_id=SUPPORT_TICKET_CLOSED_EMOJI_ID,
    )
    await event.bot.send_message(
        chat_id=group_id,
        text=CLOSE_TICKET_AFTER_USER_BANNED_BOT_MESSAGE,
        message_thread_id=ticket.message_thread_id,
    )

    key = StorageKey(event.bot.id, ticket.chat_id, event.from_user.id)
    await fsm_storage.set_state(key, None)

    ticket.closed = True
