import pytest
from aiogram.fsm.state import State
from aiogram.fsm.storage.base import BaseStorage, StorageKey
from aiogram.methods import ForwardMessage, SendMessage
from aiogram.types import Chat

from supbot import texts
from supbot.routers.support_tgm import Support
from tests.supbot.conftest import MockedBot, WebhookUpdater, id_provider
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
async def test_creating_support_ticket(
    webhook_updater: WebhookUpdater,
    mocked_bot: MockedBot,
    bot_storage: BaseStorage,
    bot_storage_key: StorageKey,
    supbot_channel_id: int,
    tg_chat_id: int,
    tg_user_id: int,
) -> None:
    message_id = id_provider.generate_id()
    await bot_storage.set_state(bot_storage_key, Support.start)

    webhook_updater(
        UpdateFactory.build(
            message=MessageFactory.build(
                message_id=message_id,
                chat=Chat(id=tg_chat_id, type="private"),
                from_user=UserFactory.build(id=tg_user_id),
            ),
        )
    )

    assert await bot_storage.get_state(bot_storage_key) == Support.conversation

    mocked_bot.assert_next_api_call(
        ForwardMessage,
        {
            "chat_id": supbot_channel_id,
            "from_chat_id": tg_chat_id,
            "message_id": message_id,
        },
    )
    mocked_bot.assert_next_api_call(
        SendMessage,
        {"chat_id": tg_chat_id, "text": texts.WAIT_SUPPORT_MESSAGE},
    )
    mocked_bot.assert_no_more_api_calls()


@pytest.mark.parametrize("state", [Support.start, Support.conversation])
@pytest.mark.anyio()
async def test_exiting_support(
    webhook_updater: WebhookUpdater,
    mocked_bot: MockedBot,
    bot_storage: BaseStorage,
    bot_storage_key: StorageKey,
    tg_chat_id: int,
    tg_user_id: int,
    state: State,
) -> None:
    await bot_storage.set_state(bot_storage_key, state)

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
            "text": texts.EXIT_SUPPORT_MESSAGE,
            "reply_markup": {"remove_keyboard": True},
        },
    )
    mocked_bot.assert_no_more_api_calls()
