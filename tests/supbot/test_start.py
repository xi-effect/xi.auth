from datetime import datetime
from typing import Annotated

import pytest
from aiogram.fsm.storage.base import BaseStorage, StorageKey
from aiogram.methods import SendMessage
from aiogram.types import Chat, Message, Update, User
from faker import Faker
from pydantic import Field

from supbot import texts
from tests.supbot.conftest import MockedBot, WebhookUpdater, id_provider

AutoID = Annotated[int, Field(default_factory=id_provider.generate_id)]


class UpdateExt(Update):  # TODO maybe use these
    update_id: AutoID


class MessageExt(Message):
    message_id: AutoID
    date: Annotated[datetime, Field(default_factory=datetime.utcnow)]


@pytest.mark.anyio()
async def test_tg_starting(
    webhook_updater: WebhookUpdater,
    mocked_bot: MockedBot,
) -> None:
    chat_id = id_provider.generate_id()

    webhook_updater(
        Update(
            update_id=id_provider.generate_id(),
            message=Message(
                message_id=id_provider.generate_id(),
                date=datetime.utcnow(),
                text="/start",
                chat=Chat(
                    id=chat_id,
                    type="private",
                ),
            ),
        )
    )

    mocked_bot.assert_next_api_call(
        SendMessage,
        {"chat_id": chat_id, "text": texts.START_MESSAGE},
    )
    mocked_bot.assert_no_more_api_calls()


@pytest.mark.parametrize(
    ("current_state", "new_state"),
    [
        pytest.param(None, "spam", id="empty_state"),
        pytest.param("spam", "eggs", id="spam_state"),
        pytest.param("eggs", "spam", id="eggs_state"),
    ],
)
@pytest.mark.anyio()
async def test_tg_echoing(
    faker: Faker,
    webhook_updater: WebhookUpdater,
    mocked_bot: MockedBot,
    bot_storage: BaseStorage,
    supbot_channel_id: int,
    current_state: str | None,
    new_state: str,
) -> None:
    # Temporary test to check mocking capabilities

    user_id = id_provider.generate_id()
    chat_id = id_provider.generate_id()
    echo_text = faker.text()
    storage_key = StorageKey(bot_id=mocked_bot.id, chat_id=chat_id, user_id=user_id)

    await bot_storage.set_state(storage_key, current_state)

    webhook_updater(
        Update(
            update_id=id_provider.generate_id(),
            message=Message(
                message_id=id_provider.generate_id(),
                text=echo_text,
                date=datetime.utcnow(),
                chat=Chat(id=chat_id, type="private"),
                from_user=User(
                    id=user_id,
                    is_bot=False,
                    first_name=faker.name(),
                ),
            ),
        )
    )

    assert await bot_storage.get_state(storage_key) == new_state

    # From context
    mocked_bot.assert_next_api_call(
        SendMessage,
        {"chat_id": chat_id, "text": str(current_state)},
    )
    # Echo to private chat
    mocked_bot.assert_next_api_call(
        SendMessage,
        {"chat_id": chat_id, "text": echo_text},
    )
    # Echo to channel
    mocked_bot.assert_next_api_call(
        SendMessage,
        {"chat_id": supbot_channel_id, "text": echo_text},
    )
    mocked_bot.assert_no_more_api_calls()
