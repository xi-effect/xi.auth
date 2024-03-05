from unittest.mock import Mock

import pytest
from discord_webhook import AsyncDiscordWebhook
from faker import Faker
from starlette.testclient import TestClient

from tests.mock_stack import MockStack
from tests.utils import assert_nodata_response, assert_response


@pytest.mark.anyio()
async def test_demo_form_submitting(
    client: TestClient,
    faker: Faker,
    mock_stack: MockStack,
) -> None:
    response_mock = Mock()
    response_mock.raise_for_status = Mock()
    execute_mock = mock_stack.enter_async_mock(
        AsyncDiscordWebhook, "execute", return_value=response_mock
    )
    mock_stack.enter_mock("app.routes.forms_rst.DEMO_WEBHOOK_URL", return_value="")

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
    client: TestClient, faker: Faker
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
