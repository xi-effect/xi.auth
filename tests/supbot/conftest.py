from collections.abc import Iterable, Sequence
from random import randint
from typing import Any, Protocol
from unittest.mock import AsyncMock

import pytest
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.methods import TelegramMethod
from aiogram.types import Update
from pydantic_marshals.contains import TypeChecker, assert_contains
from starlette.testclient import TestClient

from supbot.aiogram_extension import TelegramApp
from supbot.main import telegram_app
from tests.mock_stack import MockStack
from tests.utils import assert_nodata_response


class IDProvider:
    def __init__(self) -> None:
        self._count: int = randint(0, 10000)  # noqa: S311  # no cryptography involved

    def generate_id(self) -> int:
        self._count += 1
        return self._count


id_provider = IDProvider()


class WebhookUpdater(Protocol):
    def __call__(self, update: Update) -> None:
        pass


@pytest.fixture(scope="session")
def webhook_updater(client: TestClient) -> WebhookUpdater:
    def webhook_updater_inner(update: Update) -> None:
        assert_nodata_response(
            client.post("/api/telegram/updates/", json=update.model_dump(mode="json"))
        )

    return webhook_updater_inner


@pytest.fixture(scope="session")
def bot() -> Bot:
    return Bot(token="1:a")  # noqa S106  # not a real password, but required


@pytest.fixture(scope="session")
def base_bot_storage() -> MemoryStorage:
    return MemoryStorage()


@pytest.fixture(scope="session")
def supbot_group_id() -> int:
    return id_provider.generate_id()


@pytest.fixture(scope="session")
def supbot_channel_id() -> int:
    return id_provider.generate_id()


@pytest.fixture(autouse=True, scope="session")
def mocked_telegram_app(
    bot: Bot,
    base_bot_storage: MemoryStorage,
    supbot_group_id: int,
    supbot_channel_id: int,
) -> TelegramApp:
    telegram_app.initialize(
        bot=bot,
        dispatcher=Dispatcher(
            storage=base_bot_storage,
            group_id=supbot_group_id,
            channel_id=supbot_channel_id,
        ),
    )
    return telegram_app


class MockedBot:
    def __init__(self, bot: Bot, call_mock: AsyncMock) -> None:
        self.bot = bot
        self.call_mock = call_mock
        self.api_call_iterator = self.iter_api_calls()

    @property
    def id(self) -> int:
        return self.bot.id

    def iter_bot_calls(self) -> Iterable[tuple[Sequence[Any], dict[str, Any]]]:
        for mock_call in self.call_mock.mock_calls:
            if len(mock_call) == 2:
                yield mock_call  # type: ignore[misc]  # unittest is badly typed
            elif len(mock_call) == 3 and mock_call[0] == "":
                yield mock_call[1:]  # type: ignore[misc]  # unittest is badly typed

    def iter_api_calls(self) -> Iterable[TelegramMethod[Any]]:
        for args, _ in self.iter_bot_calls():
            assert len(args) == 1
            argument = args[0]
            assert isinstance(argument, TelegramMethod)
            yield argument

    def reset_iteration(self) -> None:
        self.api_call_iterator = self.iter_api_calls()

    def assert_next_api_call(
        self, method: type[TelegramMethod[Any]], data: TypeChecker
    ) -> None:
        argument = next(self.api_call_iterator, None)  # type: ignore[call-overload]
        if argument is None:
            raise AssertionError("Next API call not found")
        assert isinstance(argument, method)
        assert_contains(argument.model_dump(), data)

    def assert_no_more_api_calls(self) -> None:
        assert list(self.api_call_iterator) == []


@pytest.fixture()
def bot_id() -> int:
    return id_provider.generate_id()


@pytest.fixture(autouse=True)
def mocked_bot(mock_stack: MockStack, bot: Bot, bot_id: int) -> MockedBot:
    bot_call_mock = mock_stack.enter_async_mock(Bot, "__call__")
    mock_stack.enter_mock(Bot, "id", property_value=bot_id)
    return MockedBot(bot=bot, call_mock=bot_call_mock)


@pytest.fixture(autouse=True)
def bot_storage(base_bot_storage: MemoryStorage) -> Iterable[MemoryStorage]:
    yield base_bot_storage
    base_bot_storage.storage.clear()


@pytest.fixture()
def tg_user_id() -> int:
    return id_provider.generate_id()


@pytest.fixture()
def tg_chat_id() -> int:
    return id_provider.generate_id()


@pytest.fixture()
def bot_storage_key(
    mocked_bot: MockedBot,
    tg_user_id: int,
    tg_chat_id: int,
) -> StorageKey:
    return StorageKey(
        bot_id=mocked_bot.id,
        chat_id=tg_chat_id,
        user_id=tg_user_id,
    )
