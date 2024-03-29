from typing import Any

import pytest
from aiogram.fsm.state import State
from aiogram.fsm.storage.base import BaseStorage, StorageKey
from aiogram.methods import SendMessage
from aiogram.types import Chat
from faker import Faker

from supbot import texts
from supbot.routers.vacancy_tgm import VacancyApplication
from tests.mock_stack import MockStack
from tests.supbot.conftest import MockedBot, WebhookUpdater
from tests.supbot.factories import MessageFactory, UpdateFactory, UserFactory

CHOOSE_VACANCY_KEYBOARD = {
    "keyboard": [
        *[[{"text": VACANCY}] for VACANCY in texts.VACANCIES],
        [{"text": texts.EXIT}],
    ],
}
NAVIGATION_KEYBOARD = {
    "keyboard": [[{"text": texts.BACK}, {"text": texts.EXIT}]],
}
SENDING_TELEGRAM_KEYBOARD = {
    "keyboard": [
        [{"text": texts.PROVIDE_CURRENT_ACCOUNT}],
        [{"text": texts.BACK}, {"text": texts.EXIT}],
    ],
}
SENDING_INFO_KEYBOARD = {
    "keyboard": [
        [{"text": texts.SKIP}],
        [{"text": texts.BACK}, {"text": texts.EXIT}],
    ],
}
EMPTY_KEYBOARD = {"remove_keyboard": True}


@pytest.mark.anyio()
async def test_starting_vacancy_form(
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
                text="/vacancy",
                chat=Chat(id=tg_chat_id, type="private"),
                from_user=UserFactory.build(id=tg_user_id),
            ),
        )
    )

    assert (
        await bot_storage.get_state(bot_storage_key)
        == VacancyApplication.choosing_vacancy
    )

    mocked_bot.assert_next_api_call(
        SendMessage,
        {
            "chat_id": tg_chat_id,
            "text": texts.CHOOSE_VACANCY_MESSAGE,
            "reply_markup": CHOOSE_VACANCY_KEYBOARD,
        },
    )
    mocked_bot.assert_no_more_api_calls()


@pytest.mark.anyio()
async def test_sending_vacancy(
    faker: Faker,
    webhook_updater: WebhookUpdater,
    mocked_bot: MockedBot,
    bot_storage: BaseStorage,
    bot_storage_key: StorageKey,
    tg_chat_id: int,
    tg_user_id: int,
) -> None:
    await bot_storage.set_state(bot_storage_key, VacancyApplication.choosing_vacancy)
    vacancy = faker.sentence(nb_words=2)

    webhook_updater(
        UpdateFactory.build(
            message=MessageFactory.build(
                text=vacancy,
                chat=Chat(id=tg_chat_id, type="private"),
                from_user=UserFactory.build(id=tg_user_id),
            ),
        )
    )

    assert (
        await bot_storage.get_state(bot_storage_key) == VacancyApplication.sending_name
    )
    assert await bot_storage.get_data(bot_storage_key) == {"vacancy": vacancy}
    mocked_bot.assert_next_api_call(
        SendMessage,
        {
            "chat_id": tg_chat_id,
            "text": texts.SEND_NAME_MESSAGE,
            "reply_markup": NAVIGATION_KEYBOARD,
        },
    )
    mocked_bot.assert_no_more_api_calls()


@pytest.mark.anyio()
async def test_sending_name(
    faker: Faker,
    webhook_updater: WebhookUpdater,
    mocked_bot: MockedBot,
    bot_storage: BaseStorage,
    bot_storage_key: StorageKey,
    tg_chat_id: int,
    tg_user_id: int,
) -> None:
    await bot_storage.set_state(bot_storage_key, VacancyApplication.sending_name)
    name = faker.name()

    webhook_updater(
        UpdateFactory.build(
            message=MessageFactory.build(
                text=name,
                chat=Chat(id=tg_chat_id, type="private"),
                from_user=UserFactory.build(id=tg_user_id),
            ),
        )
    )

    assert (
        await bot_storage.get_state(bot_storage_key)
        == VacancyApplication.sending_telegram
    )
    assert await bot_storage.get_data(bot_storage_key) == {"name": name}
    mocked_bot.assert_next_api_call(
        SendMessage,
        {
            "chat_id": tg_chat_id,
            "text": texts.SEND_TELEGRAM_MESSAGE,
            "reply_markup": SENDING_TELEGRAM_KEYBOARD,
        },
    )
    mocked_bot.assert_no_more_api_calls()


@pytest.mark.anyio()
@pytest.mark.parametrize(
    "provide_account",
    [
        pytest.param(
            False,
            id="current_account",
        ),
        pytest.param(True, id="provided_account"),
    ],
)
async def test_sending_telegram(
    faker: Faker,
    webhook_updater: WebhookUpdater,
    mocked_bot: MockedBot,
    bot_storage: BaseStorage,
    bot_storage_key: StorageKey,
    tg_chat_id: int,
    tg_user_id: int,
    provide_account: bool,
) -> None:
    username = faker.word()
    if provide_account:
        text = faker.word()
        expected_data = {"telegram": text}
    else:
        text = texts.PROVIDE_CURRENT_ACCOUNT
        expected_data = {"telegram": f"{texts.TELEGRAM_URL}/{username}"}

    await bot_storage.set_state(bot_storage_key, VacancyApplication.sending_telegram)

    webhook_updater(
        UpdateFactory.build(
            message=MessageFactory.build(
                text=text,
                chat=Chat(id=tg_chat_id, type="private"),
                from_user=UserFactory.build(id=tg_user_id, username=username),
            ),
        )
    )

    assert (
        await bot_storage.get_state(bot_storage_key)
        == VacancyApplication.sending_resume
    )
    assert await bot_storage.get_data(bot_storage_key) == expected_data
    mocked_bot.assert_next_api_call(
        SendMessage,
        {
            "chat_id": tg_chat_id,
            "text": texts.SEND_RESUME_MESSAGE,
            "reply_markup": NAVIGATION_KEYBOARD,
        },
    )
    mocked_bot.assert_no_more_api_calls()


@pytest.mark.anyio()
async def test_sending_resume(
    faker: Faker,
    webhook_updater: WebhookUpdater,
    mocked_bot: MockedBot,
    bot_storage: BaseStorage,
    bot_storage_key: StorageKey,
    tg_chat_id: int,
    tg_user_id: int,
) -> None:
    await bot_storage.set_state(bot_storage_key, VacancyApplication.sending_resume)
    url = faker.url()
    webhook_updater(
        UpdateFactory.build(
            message=MessageFactory.build(
                text=url,
                chat=Chat(id=tg_chat_id, type="private"),
                from_user=UserFactory.build(id=tg_user_id),
            ),
        )
    )

    assert (
        await bot_storage.get_state(bot_storage_key) == VacancyApplication.sending_info
    )
    assert await bot_storage.get_data(bot_storage_key) == {"resume": url}
    mocked_bot.assert_next_api_call(
        SendMessage,
        {
            "chat_id": tg_chat_id,
            "text": texts.SEND_INFO_MESSAGE,
            "reply_markup": SENDING_INFO_KEYBOARD,
        },
    )

    mocked_bot.assert_no_more_api_calls()


@pytest.mark.anyio()
@pytest.mark.parametrize(
    "text",
    [
        pytest.param(texts.SKIP, id="skip"),
        pytest.param("my_info", id="provide_info"),
    ],
)
async def test_sending_info(
    faker: Faker,
    mock_stack: MockStack,
    webhook_updater: WebhookUpdater,
    mocked_bot: MockedBot,
    bot_storage: BaseStorage,
    bot_storage_key: StorageKey,
    tg_chat_id: int,
    tg_user_id: int,
    text: str,
) -> None:
    vacancy_endpoint_mock = mock_stack.enter_async_mock(
        "supbot.routers.vacancy_tgm.apply_for_vacancy"
    )
    data = {
        "name": faker.name(),
        "vacancy": faker.sentence(nb_words=2),
        "telegram": faker.url(),
        "resume": faker.url(),
    }
    if text != texts.SKIP:
        data["message"] = faker.paragraph(nb_sentences=5)
    await bot_storage.update_data(bot_storage_key, data)
    await bot_storage.set_state(bot_storage_key, VacancyApplication.sending_info)

    webhook_updater(
        UpdateFactory.build(
            message=MessageFactory.build(
                text=text,
                chat=Chat(id=tg_chat_id, type="private"),
                from_user=UserFactory.build(id=tg_user_id),
            ),
        )
    )

    assert await bot_storage.get_state(bot_storage_key) is None
    assert await bot_storage.get_data(bot_storage_key) == {}
    mocked_bot.assert_next_api_call(
        SendMessage,
        {
            "chat_id": tg_chat_id,
            "text": texts.VACANCY_FINAL_MESSAGE,
            "reply_markup": EMPTY_KEYBOARD,
        },
    )
    mocked_bot.assert_no_more_api_calls()
    vacancy_endpoint_mock.assert_called_once()


@pytest.mark.anyio()
@pytest.mark.parametrize(
    ("state", "expected_message", "expected_keyboard"),
    [
        pytest.param(
            VacancyApplication.sending_name,
            texts.CHOOSE_VACANCY_MESSAGE,
            CHOOSE_VACANCY_KEYBOARD,
            id="sending_name",
        ),
        pytest.param(
            VacancyApplication.sending_telegram,
            texts.SEND_NAME_MESSAGE,
            NAVIGATION_KEYBOARD,
            id="sending_telegram",
        ),
        pytest.param(
            VacancyApplication.sending_resume,
            texts.SEND_TELEGRAM_MESSAGE,
            SENDING_TELEGRAM_KEYBOARD,
            id="sending_resume",
        ),
        pytest.param(
            VacancyApplication.sending_info,
            texts.SEND_RESUME_MESSAGE,
            NAVIGATION_KEYBOARD,
            id="sending_info",
        ),
    ],
)
async def test_going_back(
    webhook_updater: WebhookUpdater,
    mocked_bot: MockedBot,
    bot_storage: BaseStorage,
    bot_storage_key: StorageKey,
    tg_chat_id: int,
    tg_user_id: int,
    state: State,
    expected_message: str,
    expected_keyboard: dict[str, Any],
) -> None:
    await bot_storage.set_state(bot_storage_key, state)

    webhook_updater(
        UpdateFactory.build(
            message=MessageFactory.build(
                text=texts.BACK,
                chat=Chat(id=tg_chat_id, type="private"),
                from_user=UserFactory.build(id=tg_user_id),
            ),
        )
    )

    mocked_bot.assert_next_api_call(
        SendMessage,
        {
            "chat_id": tg_chat_id,
            "text": expected_message,
            "reply_markup": expected_keyboard,
        },
    )
    mocked_bot.assert_no_more_api_calls()


@pytest.mark.anyio()
@pytest.mark.parametrize(
    "state",
    [
        pytest.param(VacancyApplication.choosing_vacancy, id="choosing_vacancy"),
        pytest.param(VacancyApplication.sending_name, id="sending_name"),
        pytest.param(VacancyApplication.sending_telegram, id="sending_telegram"),
        pytest.param(VacancyApplication.sending_resume, id="sending_resume"),
        pytest.param(VacancyApplication.sending_info, id="sending_info"),
    ],
)
async def test_exit(
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
                text=texts.EXIT,
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
            "text": texts.EXIT_VACANCY_FORM_MESSAGE,
            "reply_markup": EMPTY_KEYBOARD,
        },
    )
    mocked_bot.assert_no_more_api_calls()
