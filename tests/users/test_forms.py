from unittest.mock import Mock

import pytest
from discord_webhook import AsyncDiscordWebhook
from faker import Faker
from starlette.testclient import TestClient

from tests.mock_stack import MockStack
from tests.utils import assert_nodata_response, assert_response


@pytest.mark.anyio()
async def test_demo_form_submitting(
    faker: Faker, mock_stack: MockStack, client: TestClient
) -> None:
    response_mock = Mock()
    response_mock.raise_for_status = Mock()
    execute_mock = mock_stack.enter_async_mock(
        AsyncDiscordWebhook, "execute", return_value=response_mock
    )
    mock_stack.enter_mock(
        "app.users.routes.forms_rst.DEMO_WEBHOOK_URL", return_value=""
    )

    assert_nodata_response(
        client.post(
            "/api/demo-applications/",
            json={
                "name": faker.name(),
                "contacts": [faker.ascii_free_email(), faker.phone_number()],
            },
        )
    )
    execute_mock.assert_called_once()
    response_mock.raise_for_status.assert_called_once()


@pytest.mark.anyio()
async def test_demo_form_submitting_missing_webhook_url(
    faker: Faker, client: TestClient
) -> None:
    assert_response(
        client.post(
            "/api/demo-applications/",
            json={
                "name": faker.name(),
                "contacts": [faker.ascii_free_email(), faker.phone_number()],
            },
        ),
        expected_code=500,
        expected_json={"detail": "Webhook url is not set"},
    )


@pytest.mark.anyio()
async def test_vacancy_form_submitting(
    faker: Faker, mock_stack: MockStack, client: TestClient
) -> None:
    response_mock = Mock()
    response_mock.raise_for_status = Mock()
    execute_mock = mock_stack.enter_async_mock(
        AsyncDiscordWebhook, "execute", return_value=response_mock
    )
    mock_stack.enter_mock(
        "app.users.routes.forms_rst.VACANCY_WEBHOOK_URL", return_value=""
    )

    assert_nodata_response(
        client.post(
            "/api/vacancy-applications/",
            json={
                "position": faker.word(),
                "name": faker.name(),
                "telegram": faker.word(),
                "link": faker.hostname(),
                "message": faker.sentence(),
            },
        )
    )
    execute_mock.assert_called_once()
    response_mock.raise_for_status.assert_called_once()


@pytest.mark.anyio()
async def test_vacancy_form_submitting_missing_webhook_url(
    faker: Faker, client: TestClient
) -> None:
    assert_response(
        client.post(
            "/api/vacancy-applications/",
            json={
                "position": faker.word(),
                "name": faker.name(),
                "telegram": faker.word(),
                "link": faker.hostname(),
                "message": faker.sentence(),
            },
        ),
        expected_code=500,
        expected_json={"detail": "Webhook url is not set"},
    )
