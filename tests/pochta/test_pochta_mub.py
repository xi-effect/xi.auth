from email.message import EmailMessage
from unittest.mock import ANY

import pytest
from faker import Faker
from pydantic_marshals.contains import assert_contains
from starlette.testclient import TestClient

from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.mock_stack import MockStack


@pytest.fixture()
def email_form_data(faker: Faker) -> dict[str, str]:
    return {
        "receiver": faker.email(),
        "subject": faker.sentence(),
    }


@pytest.fixture()
def html_filename_and_content(faker: Faker) -> tuple[str, bytes]:
    return (
        faker.file_name(extension="html"),
        faker.sentence().encode("utf-8"),
    )


@pytest.mark.anyio()
async def test_sending_email_from_file(
    faker: Faker,
    mock_stack: MockStack,
    mub_client: TestClient,
    email_form_data: dict[str, str],
    html_filename_and_content: tuple[str, bytes],
) -> None:
    send_message_mock = mock_stack.enter_async_mock(
        "app.pochta.routes.pochta_mub.smtp_client"
    ).__aenter__.return_value.send_message
    email_username = faker.email()
    mock_stack.enter_patch(
        "app.pochta.routes.pochta_mub.EMAIL_USERNAME", new=email_username
    )

    assert_nodata_response(
        mub_client.post(
            "/mub/pochta-service/emails-from-file/",
            data=email_form_data,
            files={"file": html_filename_and_content},
        ),
    )

    send_message_mock.assert_called_once_with(ANY)
    actual_message: EmailMessage = send_message_mock.call_args[0][0]
    assert_contains(
        {
            "Headers": {key: str(value) for key, value in actual_message.items()},
            "Content": actual_message.get_content().strip(),
        },
        {
            "Headers": {
                "To": email_form_data["receiver"],
                "Subject": email_form_data["subject"],
                "From": email_username,
                "Content-Type": 'text/html; charset="utf-8"',
                "Content-Transfer-Encoding": "7bit",
                "MIME-Version": "1.0",
            },
            "Content": html_filename_and_content[1].decode("utf-8"),
        },
    )


@pytest.mark.anyio()
async def test_sending_email_from_file_config_not_set(
    mock_stack: MockStack,
    mub_client: TestClient,
    email_form_data: dict[str, str],
    html_filename_and_content: tuple[str, bytes],
) -> None:
    mock_stack.enter_patch("app.pochta.routes.pochta_mub.smtp_client", new=None)

    assert_response(
        mub_client.post(
            "/mub/pochta-service/emails-from-file/",
            data=email_form_data,
            files={"file": html_filename_and_content},
        ),
        expected_code=500,
        expected_json={"detail": "Email config is not set"},
    )
