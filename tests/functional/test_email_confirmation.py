import time
from datetime import datetime, timedelta

import pytest
from faker import Faker
from freezegun import freeze_time
from starlette.testclient import TestClient

from app.common.config import email_confirmation_cryptography, pochta_producer
from app.models.users_db import User
from tests.conftest import ActiveSession
from tests.mock_stack import MockStack
from tests.utils import assert_nodata_response, assert_response, get_db_user


@pytest.mark.anyio()
async def test_confirming_email(
    client: TestClient,
    active_session: ActiveSession,
    user: User,
) -> None:
    assert_nodata_response(
        client.post(
            "/api/email-confirmation/confirmations/",
            json={"token": email_confirmation_cryptography.encrypt(user.email)},
        ),
    )

    async with active_session():
        assert (await get_db_user(user)).email_confirmed


@pytest.mark.anyio()
async def test_confirming_email_user_not_found(
    faker: Faker,
    client: TestClient,
) -> None:
    assert_response(
        client.post(
            "/api/email-confirmation/confirmations/",
            json={"token": email_confirmation_cryptography.encrypt(faker.email())},
        ),
        expected_code=401,
        expected_json={"detail": "Invalid token"},
    )


@pytest.mark.anyio()
async def test_confirming_email_invalid_token(
    faker: Faker,
    client: TestClient,
) -> None:
    assert_response(
        client.post(
            "/api/email-confirmation/confirmations/",
            json={"token": faker.text()},
        ),
        expected_code=401,
        expected_json={"detail": "Invalid token"},
    )


@pytest.mark.anyio()
async def test_confirming_email_expired_token(
    faker: Faker,
    client: TestClient,
    user: User,
) -> None:
    expired_confirmation_token: bytes = (
        email_confirmation_cryptography.encryptor.encrypt_at_time(
            user.email.encode("utf-8"),
            current_time=int(time.time())
            - email_confirmation_cryptography.encryption_ttl
            - 1,
        )
    )

    assert_response(
        client.post(
            "/api/email-confirmation/confirmations/",
            json={"token": expired_confirmation_token.decode("utf-8")},
        ),
        expected_code=401,
        expected_json={"detail": "Invalid token"},
    )


@pytest.mark.anyio()
async def test_resending_confirmation(
    active_session: ActiveSession,
    mock_stack: MockStack,
    user: User,
    authorized_client: TestClient,
) -> None:
    pochta_mock = mock_stack.enter_async_mock(pochta_producer, "send_message")

    with freeze_time():
        assert_nodata_response(
            authorized_client.post(
                "/api/email-confirmation/requests/",
            )
        )

        pochta_mock.assert_called_once()
        async with active_session():
            assert (
                await get_db_user(user)
            ).allowed_confirmation_resend == datetime.now() + timedelta(minutes=10)


@pytest.mark.anyio()
async def test_resending_confirmation_timeout_not_passed(
    active_session: ActiveSession,
    user: User,
    authorized_client: TestClient,
) -> None:
    async with active_session():
        (await get_db_user(user)).set_confirmation_resend_timeout()

    assert_response(
        authorized_client.post(
            "/api/email-confirmation/requests/",
        ),
        expected_code=429,
        expected_json={"detail": "Too many emails"},
    )
