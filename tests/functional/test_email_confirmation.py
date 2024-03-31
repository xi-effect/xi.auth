import time

import pytest
from faker import Faker
from starlette.testclient import TestClient

from app.common.config import email_confirmation_cryptography
from app.models.users_db import User
from tests.conftest import ActiveSession
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
            json={
                "confirmation_token": email_confirmation_cryptography.encrypt(
                    user.email
                )
            },
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
            json={
                "confirmation_token": email_confirmation_cryptography.encrypt(
                    faker.email()
                )
            },
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
            json={"confirmation_token": faker.text()},
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
            json={"confirmation_token": expired_confirmation_token.decode("utf-8")},
        ),
        expected_code=401,
        expected_json={"detail": "Invalid token"},
    )
