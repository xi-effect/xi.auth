from aiogram import F, Router
from aiogram.filters import KICKED, ChatMemberUpdatedFilter, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.base import BaseStorage, StorageKey
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from app.supbot import texts
from app.supbot.models.support_db import SupportTicket
from app.supbot.utils.aiogram_ext import ChatMemberUpdatedExt, MessageExt
from app.supbot.utils.filters import SupportTicketFilter, command_filter

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
        text=texts.START_SUPPORT_MESSAGE,
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=texts.MAIN_MENU_BUTTON_TEXT)]],
            resize_keyboard=True,
        ),
    )
    await state.set_state(Support.start)


@router.message(Support.start, F.text == texts.MAIN_MENU_BUTTON_TEXT)
async def exit_support(message: MessageExt, state: FSMContext) -> None:
    await message.answer(
        text=texts.MAIN_MENU_MESSAGE,
        reply_markup=ReplyKeyboardMarkup(
            keyboard=texts.MAIN_MENU_KEYBOARD_MARKUP, resize_keyboard=True
        ),
    )
    await state.clear()


@router.message(Support.start)
async def create_support_ticket(
    message: MessageExt, state: FSMContext, group_id: int
) -> None:
    topic = await message.bot.create_forum_topic(
        chat_id=group_id,
        name=texts.SUPPORT_TOPIC_NAME_TEMPLATE.format(username=message.chat.username),
        icon_custom_emoji_id=texts.SUPPORT_TICKED_OPENED_EMOJI_ID,
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
        text=texts.WAIT_SUPPORT_MESSAGE,
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=texts.CLOSE_SUPPORT_BUTTON_TEXT)]],
            resize_keyboard=True,
        ),
    )
    await state.update_data(thread_id=topic.message_thread_id)
    await state.set_state(Support.conversation)


@router.message(
    Support.conversation,
    F.text != texts.CLOSE_SUPPORT_BUTTON_TEXT,
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
    F.text == texts.CLOSE_SUPPORT_BUTTON_TEXT,
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
        icon_custom_emoji_id=texts.SUPPORT_TICKET_CLOSED_EMOJI_ID,
    )
    await message.bot.send_message(
        chat_id=group_id,
        text=texts.TICKET_CLOSED_BY_USER_MESSAGE,
        message_thread_id=ticket.message_thread_id,
    )
    await message.answer(
        text=texts.CLOSE_TICKET_CONFIRMATION_MESSAGE,
        reply_markup=ReplyKeyboardMarkup(
            keyboard=texts.MAIN_MENU_KEYBOARD_MARKUP, resize_keyboard=True
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
        icon_custom_emoji_id=texts.SUPPORT_TICKET_CLOSED_EMOJI_ID,
    )
    await event.bot.send_message(
        chat_id=group_id,
        text=texts.TICKET_CLOSED_AFTER_USER_BANNED_BOT_MESSAGE,
        message_thread_id=ticket.message_thread_id,
    )

    key = StorageKey(event.bot.id, ticket.chat_id, event.from_user.id)
    await fsm_storage.set_state(key, None)

    ticket.closed = True
