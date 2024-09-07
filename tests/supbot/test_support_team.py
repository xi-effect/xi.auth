import pytest
from aiogram.fsm.storage.base import BaseStorage, StorageKey
from aiogram.methods import CopyMessage, EditForumTopic, SendMessage
from aiogram.methods.set_message_reaction import SetMessageReaction
from aiogram.types import Chat
from aiogram.types.forum_topic_closed import ForumTopicClosed

from app.supbot import texts
from app.supbot.models.support_db import SupportTicket
from tests.supbot.conftest import (
    EXPECTED_MAIN_MENU_KEYBOARD_MARKUP,
    MockedBot,
    WebhookUpdater,
)
from tests.supbot.factories import MessageFactory, UpdateFactory, UserFactory


@pytest.mark.anyio()
async def test_sending_message_to_user(
    webhook_updater: WebhookUpdater,
    mocked_bot: MockedBot,
    bot_storage: BaseStorage,
    bot_storage_key: StorageKey,
    supbot_group_id: int,
    tg_chat_id: int,
    tg_user_id: int,
    message_id: int,
    support_ticket: SupportTicket,
) -> None:
    await bot_storage.update_data(
        bot_storage_key, {"thread_id": support_ticket.message_thread_id}
    )

    webhook_updater(
        UpdateFactory.build(
            message=MessageFactory.build(
                message_id=message_id,
                message_thread_id=support_ticket.message_thread_id,
                chat=Chat(id=supbot_group_id, type="supergroup"),
                from_user=UserFactory.build(id=tg_user_id),
            ),
        ),
    )

    mocked_bot.assert_next_api_call(
        CopyMessage,
        {
            "chat_id": tg_chat_id,
            "from_chat_id": supbot_group_id,
        },
    )
    mocked_bot.assert_next_api_call(
        SetMessageReaction,
        {
            "chat_id": supbot_group_id,
            "message_id": message_id,
            "reaction": [{"emoji": texts.SUPPORT_ANSWER_DELIVERED_EMOJI}],
        },
    )
    mocked_bot.assert_no_more_api_calls()


@pytest.mark.anyio()
async def test_closing_ticket_by_support(
    webhook_updater: WebhookUpdater,
    mocked_bot: MockedBot,
    bot_storage: BaseStorage,
    bot_storage_key: StorageKey,
    supbot_group_id: int,
    tg_chat_id: int,
    tg_user_id: int,
    support_ticket: SupportTicket,
) -> None:
    webhook_updater(
        UpdateFactory.build(
            message=MessageFactory.build(
                forum_topic_closed=ForumTopicClosed(),
                message_thread_id=support_ticket.message_thread_id,
                chat=Chat(id=supbot_group_id, type="supergroup"),
                from_user=UserFactory.build(id=tg_user_id, first_name="Group"),
            ),
        ),
    )

    assert await bot_storage.get_state(bot_storage_key) is None

    mocked_bot.assert_next_api_call(
        SendMessage,
        {
            "chat_id": tg_chat_id,
            "text": texts.TICKET_CLOSED_BY_SUPPORT_MESSAGE,
            "reply_markup": EXPECTED_MAIN_MENU_KEYBOARD_MARKUP,
        },
    )
    mocked_bot.assert_next_api_call(
        EditForumTopic,
        {
            "chat_id": supbot_group_id,
            "message_thread_id": support_ticket.message_thread_id,
            "icon_custom_emoji_id": texts.SUPPORT_TICKET_CLOSED_EMOJI_ID,
        },
    )
    mocked_bot.assert_no_more_api_calls()
