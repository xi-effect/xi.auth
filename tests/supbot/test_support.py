import pytest
from aiogram import Bot
from aiogram.fsm.storage.base import BaseStorage, StorageKey
from aiogram.methods import CloseForumTopic, CopyMessage, EditForumTopic, SendMessage
from aiogram.types import Chat
from aiogram.types.forum_topic import ForumTopic
from faker import Faker

from supbot import texts
from supbot.models.support_db import SupportTicket
from supbot.routers.support_tgm import Support
from tests.mock_stack import MockStack
from tests.supbot.conftest import MockedBot, WebhookUpdater
from tests.supbot.factories import MessageFactory, UpdateFactory, UserFactory


@pytest.mark.anyio()
async def test_starting_support(
    webhook_updater: WebhookUpdater,
    mocked_bot: MockedBot,
    bot_storage: BaseStorage,
    bot_storage_key: StorageKey,
    tg_chat_id: int,
    tg_user_id: int,
) -> None:
    webhook_updater(
        UpdateFactory.build(
            message=MessageFactory.build(
                text="/support",
                chat=Chat(id=tg_chat_id, type="private"),
                from_user=UserFactory.build(id=tg_user_id),
            ),
        )
    )

    assert await bot_storage.get_state(bot_storage_key) == Support.start

    mocked_bot.assert_next_api_call(
        SendMessage,
        {
            "chat_id": tg_chat_id,
            "text": texts.START_SUPPORT_MESSAGE,
            "reply_markup": {
                "keyboard": [[{"text": texts.MAIN_MENU_BUTTON_TEXT}]],
            },
        },
    )
    mocked_bot.assert_no_more_api_calls()


@pytest.mark.anyio()
async def test_exiting_support(
    webhook_updater: WebhookUpdater,
    mocked_bot: MockedBot,
    bot_storage: BaseStorage,
    bot_storage_key: StorageKey,
    tg_chat_id: int,
    tg_user_id: int,
) -> None:
    await bot_storage.set_state(bot_storage_key, Support.start)

    webhook_updater(
        UpdateFactory.build(
            message=MessageFactory.build(
                text=texts.MAIN_MENU_BUTTON_TEXT,
                chat=Chat(id=tg_chat_id, type="private"),
                from_user=UserFactory.build(id=tg_user_id),
            ),
        )
    )

    assert await bot_storage.get_state(bot_storage_key) is None

    mocked_bot.assert_next_api_call(
        SendMessage,
        {
            "chat_id": tg_chat_id,
            "text": texts.MAIN_MENU_MESSAGE,
            "reply_markup": {"remove_keyboard": True},
        },
    )
    mocked_bot.assert_no_more_api_calls()


@pytest.mark.anyio()
async def test_creating_support_ticket(
    faker: Faker,
    mock_stack: MockStack,
    webhook_updater: WebhookUpdater,
    bot: Bot,
    mocked_bot: MockedBot,
    bot_storage: BaseStorage,
    bot_storage_key: StorageKey,
    supbot_group_id: int,
    message_thread_id: int,
    tg_chat_id: int,
    tg_user_id: int,
) -> None:
    topic_mock = mock_stack.enter_async_mock(
        bot,
        "create_forum_topic",
        return_value=ForumTopic(
            message_thread_id=message_thread_id,
            name=faker.name(),
            icon_color=faker.pyint(),
        ),
    )

    await bot_storage.set_state(bot_storage_key, Support.start)

    webhook_updater(
        UpdateFactory.build(
            message=MessageFactory.build(
                chat=Chat(id=tg_chat_id, type="private"),
                from_user=UserFactory.build(id=tg_user_id),
            ),
        ),
    )

    topic_mock.assert_called_once()

    assert await bot_storage.get_state(bot_storage_key) == Support.conversation

    mocked_bot.assert_next_api_call(
        CopyMessage,
        {
            "chat_id": supbot_group_id,
            "from_chat_id": tg_chat_id,
            "message_thread_id": message_thread_id,
        },
    )
    mocked_bot.assert_next_api_call(
        SendMessage,
        {
            "chat_id": tg_chat_id,
            "text": texts.WAIT_SUPPORT_MESSAGE,
            "reply_markup": {
                "keyboard": [[{"text": texts.CLOSE_SUPPORT_BUTTON_TEXT}]],
            },
        },
    )
    mocked_bot.assert_no_more_api_calls()


@pytest.mark.anyio()
async def test_sending_message_to_support(
    webhook_updater: WebhookUpdater,
    mocked_bot: MockedBot,
    bot_storage: BaseStorage,
    bot_storage_key: StorageKey,
    supbot_group_id: int,
    tg_chat_id: int,
    tg_user_id: int,
    support_ticket: SupportTicket,
) -> None:
    await bot_storage.update_data(
        bot_storage_key, {"thread_id": support_ticket.message_thread_id}
    )
    await bot_storage.set_state(bot_storage_key, Support.conversation)

    webhook_updater(
        UpdateFactory.build(
            message=MessageFactory.build(
                chat=Chat(id=tg_chat_id, type="private"),
                from_user=UserFactory.build(id=tg_user_id),
            ),
        ),
    )

    mocked_bot.assert_next_api_call(
        CopyMessage,
        {
            "chat_id": supbot_group_id,
            "from_chat_id": tg_chat_id,
            "message_thread_id": support_ticket.message_thread_id,
        },
    )
    mocked_bot.assert_no_more_api_calls()


@pytest.mark.anyio()
async def test_closing_support_ticket_by_user(
    webhook_updater: WebhookUpdater,
    mocked_bot: MockedBot,
    bot_storage: BaseStorage,
    bot_storage_key: StorageKey,
    supbot_group_id: int,
    tg_chat_id: int,
    tg_user_id: int,
    support_ticket: SupportTicket,
) -> None:
    await bot_storage.update_data(
        bot_storage_key, {"thread_id": support_ticket.message_thread_id}
    )
    await bot_storage.set_state(bot_storage_key, Support.conversation)

    webhook_updater(
        UpdateFactory.build(
            message=MessageFactory.build(
                text=texts.CLOSE_SUPPORT_BUTTON_TEXT,
                chat=Chat(id=tg_chat_id, type="private"),
                from_user=UserFactory.build(id=tg_user_id),
            ),
        ),
    )

    assert await bot_storage.get_state(bot_storage_key) is None

    mocked_bot.assert_next_api_call(
        CloseForumTopic,
        {
            "chat_id": supbot_group_id,
            "message_thread_id": support_ticket.message_thread_id,
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
    mocked_bot.assert_next_api_call(
        SendMessage,
        {
            "chat_id": supbot_group_id,
            "text": texts.CLOSE_SUPPORT_BY_USER_MESSAGE,
            "message_thread_id": support_ticket.message_thread_id,
        },
    )
    mocked_bot.assert_next_api_call(
        SendMessage,
        {
            "chat_id": tg_chat_id,
            "text": texts.CANCEL_SUPPORT_MESSAGE,
            "reply_markup": {"remove_keyboard": True},
        },
    )
    mocked_bot.assert_no_more_api_calls()
